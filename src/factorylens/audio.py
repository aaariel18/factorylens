from __future__ import annotations

import re
import shutil
import subprocess
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, Protocol

from .events import EventType, Evidence, MachineEvent
from .sources.rtsp import redact_rtsp_uri


class AudioCaptureError(RuntimeError):
    """Raised when an operator audio note cannot be captured safely."""


class ProcessLike(Protocol):
    stderr: IO[str] | None
    returncode: int | None

    def poll(self) -> int | None: ...

    def wait(self, timeout: float | None = None) -> int: ...

    def terminate(self) -> None: ...

    def kill(self) -> None: ...


ProcessFactory = Callable[..., ProcessLike]


@dataclass(frozen=True, slots=True)
class AudioCaptureConfig:
    max_seconds: float = 120.0
    sample_rate: int = 16000
    channels: int = 1
    rtsp_transport: str = "tcp"
    silence_seconds: float | None = 3.0
    silence_threshold_db: float = -35.0
    start_grace_seconds: float = 10.0
    terminate_grace_seconds: float = 3.0

    def __post_init__(self) -> None:
        if self.max_seconds <= 0:
            raise ValueError("max_seconds must be > 0")
        if self.sample_rate <= 0:
            raise ValueError("sample_rate must be > 0")
        if self.channels <= 0:
            raise ValueError("channels must be > 0")
        if self.silence_seconds is not None and self.silence_seconds <= 0:
            raise ValueError("silence_seconds must be > 0 or None")
        if self.start_grace_seconds < 0:
            raise ValueError("start_grace_seconds must be >= 0")
        if self.terminate_grace_seconds <= 0:
            raise ValueError("terminate_grace_seconds must be > 0")


@dataclass(frozen=True, slots=True)
class AudioCaptureResult:
    path: Path
    source_id: str
    source_uri: str
    started_at: datetime
    finished_at: datetime
    elapsed_seconds: float
    stop_reason: str
    sample_rate: int
    channels: int
    ffmpeg_exit_code: int

    def to_event(self, machine_id: str, machine_type: str = "cnc_milling") -> MachineEvent:
        return MachineEvent(
            event_type=EventType.OPERATOR_NOTE_CAPTURED,
            machine_id=machine_id,
            machine_type=machine_type,
            timestamp=self.finished_at,
            data={
                "source_id": self.source_id,
                "source_uri": self.source_uri,
                "elapsed_seconds": self.elapsed_seconds,
                "stop_reason": self.stop_reason,
                "sample_rate": self.sample_rate,
                "channels": self.channels,
            },
            evidence=(
                Evidence(
                    kind="audio",
                    uri=str(self.path),
                    media_type="audio/wav",
                ),
            ),
        )


_RTSP_TOKEN = re.compile(r"rtsp://[^\s\"']+", re.IGNORECASE)
_SILENCE_START = re.compile(r"silence_start:\s*(?P<seconds>\d+(?:\.\d+)?)")


def sanitize_ffmpeg_text(text: str) -> str:
    """Redact credentials from RTSP URLs that FFmpeg may echo to stderr."""

    def replace(match: re.Match[str]) -> str:
        token = match.group(0).rstrip(",.;)")
        suffix = match.group(0)[len(token) :]
        return redact_rtsp_uri(token) + suffix

    return _RTSP_TOKEN.sub(replace, text)


class FFmpegRTSPAudioCapture:
    """Capture a bounded operator voice note from an RTSP audio track via FFmpeg."""

    def __init__(
        self,
        uri: str,
        *,
        source_id: str = "camera",
        config: AudioCaptureConfig | None = None,
        ffmpeg_binary: str | None = None,
        process_factory: ProcessFactory = subprocess.Popen,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if not uri:
            raise ValueError("uri must not be empty")
        self.uri = uri
        self.safe_uri = redact_rtsp_uri(uri)
        self.source_id = source_id
        self.config = config or AudioCaptureConfig()
        self.ffmpeg_binary = ffmpeg_binary
        self.process_factory = process_factory
        self.clock = clock

    def resolve_ffmpeg(self) -> str:
        binary = self.ffmpeg_binary or shutil.which("ffmpeg")
        if not binary:
            raise AudioCaptureError(
                "FFmpeg was not found. Install ffmpeg and ensure it is available on PATH."
            )
        return binary

    def build_command(self, output_path: str | Path) -> list[str]:
        output = Path(output_path)
        command = [
            self.resolve_ffmpeg(),
            "-hide_banner",
            "-loglevel",
            "info",
            "-nostdin",
            "-y",
            "-rtsp_transport",
            self.config.rtsp_transport,
            "-i",
            self.uri,
            "-map",
            "0:a:0?",
            "-vn",
            "-ac",
            str(self.config.channels),
            "-ar",
            str(self.config.sample_rate),
            "-c:a",
            "pcm_s16le",
        ]
        if self.config.silence_seconds is not None:
            command.extend(
                [
                    "-af",
                    (
                        "silencedetect="
                        f"noise={self.config.silence_threshold_db}dB:"
                        f"d={self.config.silence_seconds}"
                    ),
                ]
            )
        command.extend(["-t", str(self.config.max_seconds), str(output)])
        return command

    def _finish_process(self, process: ProcessLike, *, terminate: bool) -> int:
        if terminate and process.poll() is None:
            process.terminate()
        try:
            return process.wait(timeout=self.config.terminate_grace_seconds)
        except subprocess.TimeoutExpired:
            process.kill()
            return process.wait(timeout=self.config.terminate_grace_seconds)

    def capture(self, output_path: str | Path) -> AudioCaptureResult:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        command = self.build_command(output)
        started_at = datetime.now(UTC)
        started_clock = self.clock()
        stop_reason = "max_duration"
        stderr_lines: list[str] = []

        process = self.process_factory(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        if process.stderr is not None:
            for raw_line in process.stderr:
                line = sanitize_ffmpeg_text(raw_line.rstrip())
                stderr_lines.append(line)
                if self.config.silence_seconds is None:
                    continue
                match = _SILENCE_START.search(line)
                if match is None:
                    continue
                silence_start = float(match.group("seconds"))
                silence_confirmed_at = silence_start + self.config.silence_seconds
                if silence_confirmed_at >= self.config.start_grace_seconds:
                    stop_reason = "silence"
                    break

        exit_code = self._finish_process(process, terminate=stop_reason == "silence")
        finished_clock = self.clock()
        finished_at = datetime.now(UTC)
        elapsed = max(finished_clock - started_clock, 0.0)

        if exit_code != 0 and stop_reason != "silence":
            safe_stderr = "\n".join(stderr_lines[-12:])
            lowered = safe_stderr.lower()
            if "does not contain any stream" in lowered or "matches no streams" in lowered:
                raise AudioCaptureError(
                    "The RTSP source did not expose a usable audio stream. "
                    f"Source: {self.safe_uri}"
                )
            raise AudioCaptureError(
                f"FFmpeg audio capture failed with exit code {exit_code}. "
                f"Source: {self.safe_uri}\n{safe_stderr}"
            )

        if not output.exists() or output.stat().st_size == 0:
            raise AudioCaptureError(
                "Audio capture finished without a usable output file. "
                f"Confirm the camera exposes RTSP audio. Source: {self.safe_uri}"
            )

        return AudioCaptureResult(
            path=output,
            source_id=self.source_id,
            source_uri=self.safe_uri,
            started_at=started_at,
            finished_at=finished_at,
            elapsed_seconds=elapsed,
            stop_reason=stop_reason,
            sample_rate=self.config.sample_rate,
            channels=self.config.channels,
            ffmpeg_exit_code=exit_code,
        )
