from __future__ import annotations

import math
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit


class CaptureLike(Protocol):
    def isOpened(self) -> bool: ...

    def read(self) -> tuple[bool, Any]: ...

    def get(self, prop_id: int) -> float: ...

    def release(self) -> None: ...


CaptureFactory = Callable[[str], CaptureLike]
Sleeper = Callable[[float], None]


@dataclass(frozen=True, slots=True)
class FramePacket:
    """One decoded frame plus source timing metadata."""

    frame: Any
    timestamp: datetime
    source_id: str
    source_uri: str
    capture_fps: float | None
    measured_fps: float | None
    sequence: int


def redact_rtsp_uri(uri: str) -> str:
    """Remove credentials from an RTSP URI before it reaches logs or metadata."""

    parsed = urlsplit(uri)
    if parsed.scheme.lower() not in {"rtsp", "rtsps"}:
        return uri

    hostname = parsed.hostname or ""
    if parsed.port is not None:
        hostname = f"{hostname}:{parsed.port}"

    if parsed.username is not None or parsed.password is not None:
        netloc = f"***:***@{hostname}"
    else:
        netloc = hostname

    return urlunsplit((parsed.scheme, netloc, parsed.path, parsed.query, parsed.fragment))


def _default_capture_factory(uri: str) -> CaptureLike:
    try:
        import cv2
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "OpenCV is required for RTSP capture. Install FactoryLens with the camera extra: "
            "python -m pip install -e '.[camera]'"
        ) from exc

    return cv2.VideoCapture(uri)


def _normalise_fps(value: float | int | None) -> float | None:
    if value is None:
        return None
    fps = float(value)
    if math.isnan(fps) or fps <= 0:
        return None
    return fps


class RTSPSource:
    """Reconnect-capable RTSP frame source with credential-safe metadata.

    The adapter intentionally does not perform inference. Its job is to decode frames,
    timestamp them, expose source metadata, and recover from transient stream failures.
    """

    def __init__(
        self,
        uri: str,
        *,
        source_id: str = "rtsp-camera",
        reconnect_delay_seconds: float = 1.0,
        reconnect_attempts: int = 3,
        capture_factory: CaptureFactory | None = None,
        sleeper: Sleeper = time.sleep,
    ) -> None:
        if not uri:
            raise ValueError("RTSP URI must not be empty")
        if reconnect_delay_seconds < 0:
            raise ValueError("reconnect_delay_seconds must be >= 0")
        if reconnect_attempts < 0:
            raise ValueError("reconnect_attempts must be >= 0")

        self.uri = uri
        self.safe_uri = redact_rtsp_uri(uri)
        self.source_id = source_id
        self.reconnect_delay_seconds = reconnect_delay_seconds
        self.reconnect_attempts = reconnect_attempts
        self.capture_factory = capture_factory or _default_capture_factory
        self.sleeper = sleeper

        self._capture: CaptureLike | None = None
        self._capture_fps: float | None = None
        self._sequence = 0
        self._started_at: float | None = None

    @property
    def capture_fps(self) -> float | None:
        return self._capture_fps

    @property
    def is_open(self) -> bool:
        return self._capture is not None and self._capture.isOpened()

    def open(self) -> None:
        self.close()
        capture = self.capture_factory(self.uri)
        if not capture.isOpened():
            capture.release()
            raise ConnectionError(f"Unable to open RTSP source: {self.safe_uri}")

        self._capture = capture
        # OpenCV CAP_PROP_FPS is property id 5. Using the numeric id keeps tests and
        # lightweight environments independent from importing cv2 at module import time.
        self._capture_fps = _normalise_fps(capture.get(5))
        if self._started_at is None:
            self._started_at = time.perf_counter()

    def close(self) -> None:
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _reconnect(self) -> None:
        self.close()
        last_error: Exception | None = None

        for attempt in range(self.reconnect_attempts + 1):
            if attempt > 0 or self.reconnect_delay_seconds > 0:
                self.sleeper(self.reconnect_delay_seconds)
            try:
                self.open()
                return
            except ConnectionError as exc:
                last_error = exc

        raise ConnectionError(
            f"RTSP source unavailable after reconnect attempts: {self.safe_uri}"
        ) from last_error

    def _measured_fps(self) -> float | None:
        if self._started_at is None or self._sequence <= 1:
            return None
        elapsed = time.perf_counter() - self._started_at
        if elapsed <= 0:
            return None
        return self._sequence / elapsed

    def read(self) -> FramePacket:
        if not self.is_open:
            self.open()

        assert self._capture is not None
        ok, frame = self._capture.read()
        if not ok or frame is None:
            self._reconnect()
            assert self._capture is not None
            ok, frame = self._capture.read()
            if not ok or frame is None:
                raise ConnectionError(f"RTSP frame read failed: {self.safe_uri}")

        self._sequence += 1
        return FramePacket(
            frame=frame,
            timestamp=datetime.now(UTC),
            source_id=self.source_id,
            source_uri=self.safe_uri,
            capture_fps=self._capture_fps,
            measured_fps=self._measured_fps(),
            sequence=self._sequence,
        )

    def frames(self, *, max_frames: int | None = None) -> Iterator[FramePacket]:
        if max_frames is not None and max_frames < 0:
            raise ValueError("max_frames must be >= 0 or None")

        yielded = 0
        while max_frames is None or yielded < max_frames:
            yield self.read()
            yielded += 1

    def __enter__(self) -> RTSPSource:
        self.open()
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
