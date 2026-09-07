from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Protocol

from .events import EventType, Evidence, MachineEvent
from .sources.rtsp import FramePacket


class VideoSink(Protocol):
    def write(self, frame: Any) -> None: ...

    def close(self) -> None: ...


class EvidenceBackend(Protocol):
    def save_image(self, path: Path, frame: Any) -> None: ...

    def open_video(self, path: Path, *, fps: float, frame: Any) -> VideoSink: ...


class _OpenCVVideoSink:
    def __init__(self, writer: Any) -> None:
        self._writer = writer

    def write(self, frame: Any) -> None:
        self._writer.write(frame)

    def close(self) -> None:
        self._writer.release()


class OpenCVEvidenceBackend:
    """Default image/video backend, imported lazily so the core stays lightweight."""

    def __init__(self, *, fourcc: str = "mp4v") -> None:
        if len(fourcc) != 4:
            raise ValueError("fourcc must contain exactly four characters")
        self.fourcc = fourcc

    @staticmethod
    def _cv2() -> Any:
        try:
            import cv2
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "OpenCV is required for image/video evidence. Install FactoryLens with "
                "the camera extra: python -m pip install -e '.[camera]'"
            ) from exc
        return cv2

    def save_image(self, path: Path, frame: Any) -> None:
        cv2 = self._cv2()
        path.parent.mkdir(parents=True, exist_ok=True)
        if not cv2.imwrite(str(path), frame):
            raise OSError(f"failed to write snapshot: {path}")

    def open_video(self, path: Path, *, fps: float, frame: Any) -> VideoSink:
        cv2 = self._cv2()
        path.parent.mkdir(parents=True, exist_ok=True)
        height, width = frame.shape[:2]
        writer = cv2.VideoWriter(
            str(path),
            cv2.VideoWriter_fourcc(*self.fourcc),
            fps,
            (width, height),
        )
        if not writer.isOpened():
            writer.release()
            raise OSError(f"failed to open video writer: {path}")
        return _OpenCVVideoSink(writer)


@dataclass(frozen=True, slots=True)
class EvidenceRecorderConfig:
    root_dir: Path = Path("data/jobs")
    pre_roll_seconds: float = 5.0
    snapshot_offsets_seconds: tuple[float, ...] = (0.0, 2.0, 10.0)
    default_fps: float = 15.0
    video_filename: str = "cycle.mp4"
    manifest_filename: str = "manifest.json"

    def __post_init__(self) -> None:
        if self.pre_roll_seconds < 0:
            raise ValueError("pre_roll_seconds must be >= 0")
        if self.default_fps <= 0:
            raise ValueError("default_fps must be > 0")
        if any(offset < 0 for offset in self.snapshot_offsets_seconds):
            raise ValueError("snapshot offsets must be >= 0")


@dataclass(frozen=True, slots=True)
class JobEvidenceResult:
    job_dir: Path
    manifest_path: Path
    video_path: Path
    events: tuple[MachineEvent, ...]


@dataclass(slots=True)
class JobEvidenceRecorder:
    machine_id: str
    machine_type: str = "unknown"
    job: dict[str, Any] = field(default_factory=dict)
    config: EvidenceRecorderConfig = field(default_factory=EvidenceRecorderConfig)
    backend: EvidenceBackend = field(default_factory=OpenCVEvidenceBackend)
    _buffer: deque[FramePacket] = field(init=False, default_factory=deque, repr=False)
    _events: list[MachineEvent] = field(init=False, default_factory=list, repr=False)
    _video_sink: VideoSink | None = field(init=False, default=None, repr=False)
    _video_path: Path | None = field(init=False, default=None, repr=False)
    _job_dir: Path | None = field(init=False, default=None, repr=False)
    _cycle_started_at: datetime | None = field(init=False, default=None, repr=False)
    _captured_offsets: set[float] = field(init=False, default_factory=set, repr=False)

    def __post_init__(self) -> None:
        if not self.machine_id.strip():
            raise ValueError("machine_id must not be empty")

    @property
    def active(self) -> bool:
        return self._video_sink is not None

    @property
    def job_dir(self) -> Path | None:
        return self._job_dir

    def attach_event(self, event: MachineEvent) -> None:
        self._events.append(event)

    def _prune_buffer(self, now: datetime) -> None:
        cutoff = now - timedelta(seconds=self.config.pre_roll_seconds)
        while self._buffer and self._buffer[0].timestamp < cutoff:
            self._buffer.popleft()

    def ingest(self, packet: FramePacket) -> tuple[MachineEvent, ...]:
        self._buffer.append(packet)
        self._prune_buffer(packet.timestamp)

        if not self.active:
            return ()

        assert self._video_sink is not None
        self._video_sink.write(packet.frame)
        return self._capture_due_snapshots(packet)

    def _new_job_dir(self, timestamp: datetime) -> Path:
        stamp = timestamp.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")
        return self.config.root_dir / f"{self.machine_id}_{stamp}"

    def _snapshot_event(self, packet: FramePacket, offset: float) -> MachineEvent:
        assert self._job_dir is not None
        filename = f"start_{round(offset):03d}s.jpg"
        path = self._job_dir / filename
        self.backend.save_image(path, packet.frame)
        event = MachineEvent(
            event_type=EventType.SNAPSHOT_CAPTURED,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            timestamp=packet.timestamp,
            job=dict(self.job),
            data={
                "offset_seconds": offset,
                "source_id": packet.source_id,
                "frame_sequence": packet.sequence,
            },
            evidence=(Evidence(kind="snapshot", uri=str(path), media_type="image/jpeg"),),
        )
        self._events.append(event)
        self._captured_offsets.add(offset)
        return event

    def _capture_due_snapshots(self, packet: FramePacket) -> tuple[MachineEvent, ...]:
        assert self._cycle_started_at is not None
        elapsed = max((packet.timestamp - self._cycle_started_at).total_seconds(), 0.0)
        emitted: list[MachineEvent] = []
        for offset in sorted(self.config.snapshot_offsets_seconds):
            if offset in self._captured_offsets or elapsed < offset:
                continue
            emitted.append(self._snapshot_event(packet, offset))
        return tuple(emitted)

    def start_cycle(self, event: MachineEvent) -> tuple[MachineEvent, ...]:
        if event.event_type is not EventType.MACHINE_CYCLE_STARTED:
            raise ValueError("start_cycle requires a MACHINE_CYCLE_STARTED event")
        if self.active:
            raise RuntimeError("evidence recording is already active")
        if not self._buffer:
            raise RuntimeError("at least one buffered frame is required before cycle start")

        self.job = dict(event.job or self.job)
        self._cycle_started_at = event.timestamp
        self._job_dir = self._new_job_dir(event.timestamp)
        self._job_dir.mkdir(parents=True, exist_ok=True)
        self._captured_offsets.clear()
        self._events.append(event)

        latest = self._buffer[-1]
        fps = latest.capture_fps or self.config.default_fps
        self._video_path = self._job_dir / self.config.video_filename
        self._video_sink = self.backend.open_video(
            self._video_path,
            fps=fps,
            frame=latest.frame,
        )

        buffered = tuple(self._buffer)
        for packet in buffered:
            self._video_sink.write(packet.frame)

        video_event = MachineEvent(
            event_type=EventType.VIDEO_RECORDING_STARTED,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            timestamp=event.timestamp,
            job=dict(self.job),
            data={
                "pre_roll_seconds": self.config.pre_roll_seconds,
                "pre_roll_frames": len(buffered),
                "fps": fps,
            },
            evidence=(
                Evidence(kind="video", uri=str(self._video_path), media_type="video/mp4"),
            ),
        )
        self._events.append(video_event)

        emitted: list[MachineEvent] = [video_event]
        if 0.0 in self.config.snapshot_offsets_seconds:
            emitted.append(self._snapshot_event(latest, 0.0))
        return tuple(emitted)

    def finish_cycle(self, event: MachineEvent) -> JobEvidenceResult:
        if event.event_type is not EventType.MACHINE_CYCLE_FINISHED:
            raise ValueError("finish_cycle requires a MACHINE_CYCLE_FINISHED event")
        if not self.active or self._video_sink is None:
            raise RuntimeError("evidence recording is not active")
        assert self._job_dir is not None
        assert self._video_path is not None

        self._events.append(event)
        self._video_sink.close()
        self._video_sink = None

        finish_event = MachineEvent(
            event_type=EventType.VIDEO_RECORDING_FINISHED,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            timestamp=event.timestamp,
            job=dict(self.job),
            evidence=(
                Evidence(kind="video", uri=str(self._video_path), media_type="video/mp4"),
            ),
        )
        self._events.append(finish_event)

        manifest = {
            "schema_version": "0.1",
            "machine": {"id": self.machine_id, "type": self.machine_type},
            "job": dict(self.job),
            "created_at": datetime.now(UTC).isoformat(),
            "video": str(self._video_path),
            "events": [item.to_dict() for item in self._events],
        }
        manifest_path = self._job_dir / self.config.manifest_filename
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

        result = JobEvidenceResult(
            job_dir=self._job_dir,
            manifest_path=manifest_path,
            video_path=self._video_path,
            events=tuple(self._events),
        )
        self._events.clear()
        self._captured_offsets.clear()
        self._cycle_started_at = None
        self._video_path = None
        self._job_dir = None
        return result
