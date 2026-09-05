from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Protocol

from .sources.rtsp import FramePacket


class FrameSourceLike(Protocol):
    source_id: str
    safe_uri: str

    def read(self) -> FramePacket: ...


SnapshotWriter = Callable[[Any, Path], None]
Clock = Callable[[], float]


@dataclass(frozen=True, slots=True)
class RTSPValidationReport:
    """Credential-safe summary from a short RTSP field-validation run."""

    source_id: str
    source_uri: str
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    frames_read: int
    first_sequence: int | None
    last_sequence: int | None
    capture_fps: float | None
    measured_fps: float | None
    observed_read_fps: float | None
    snapshot_path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["started_at"] = self.started_at.isoformat()
        payload["finished_at"] = self.finished_at.isoformat()
        return payload

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json() + "\n", encoding="utf-8")
        return output


def _default_snapshot_writer(frame: Any, path: Path) -> None:
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "OpenCV is required to save snapshots. Install FactoryLens with the camera extra."
        ) from exc

    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), frame):
        raise OSError(f"Unable to write snapshot: {path}")


def validate_rtsp_source(
    source: FrameSourceLike,
    *,
    duration_seconds: float | None = 30.0,
    max_frames: int | None = None,
    snapshot_path: str | Path | None = None,
    snapshot_writer: SnapshotWriter = _default_snapshot_writer,
    clock: Clock = time.perf_counter,
) -> RTSPValidationReport:
    """Read a real source for a bounded period and return useful field metrics.

    At least one bound must be configured. The function never serializes the raw RTSP URL;
    callers receive only the credential-redacted ``safe_uri`` exposed by ``RTSPSource``.
    """

    if duration_seconds is not None and duration_seconds < 0:
        raise ValueError("duration_seconds must be >= 0 or None")
    if max_frames is not None and max_frames <= 0:
        raise ValueError("max_frames must be > 0 or None")
    if duration_seconds is None and max_frames is None:
        raise ValueError("duration_seconds or max_frames must bound validation")

    started_at = datetime.now(UTC)
    started_clock = clock()
    first_packet: FramePacket | None = None
    last_packet: FramePacket | None = None
    frames_read = 0
    saved_snapshot: str | None = None

    while True:
        elapsed = clock() - started_clock
        if frames_read > 0 and duration_seconds is not None and elapsed >= duration_seconds:
            break
        if max_frames is not None and frames_read >= max_frames:
            break

        packet = source.read()
        frames_read += 1
        if first_packet is None:
            first_packet = packet
        last_packet = packet

        if frames_read == 1 and snapshot_path is not None:
            snapshot = Path(snapshot_path)
            snapshot_writer(packet.frame, snapshot)
            saved_snapshot = str(snapshot)

    finished_clock = clock()
    finished_at = datetime.now(UTC)
    elapsed_seconds = max(finished_clock - started_clock, 0.0)
    observed_read_fps = frames_read / elapsed_seconds if elapsed_seconds > 0 else None

    return RTSPValidationReport(
        source_id=source.source_id,
        source_uri=source.safe_uri,
        started_at=started_at,
        finished_at=finished_at,
        elapsed_seconds=elapsed_seconds,
        frames_read=frames_read,
        first_sequence=first_packet.sequence if first_packet else None,
        last_sequence=last_packet.sequence if last_packet else None,
        capture_fps=last_packet.capture_fps if last_packet else None,
        measured_fps=last_packet.measured_fps if last_packet else None,
        observed_read_fps=observed_read_fps,
        snapshot_path=saved_snapshot,
    )
