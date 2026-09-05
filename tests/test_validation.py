from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from factorylens.sources.rtsp import FramePacket
from factorylens.validation import validate_rtsp_source


class StepClock:
    def __init__(self, step: float = 0.1) -> None:
        self.value = 0.0
        self.step = step

    def __call__(self) -> float:
        current = self.value
        self.value += self.step
        return current


class FakeSource:
    source_id = "cnc-03-spindle"
    safe_uri = "rtsp://***:***@192.0.2.10:554/stream1"

    def __init__(self) -> None:
        self.sequence = 0

    def read(self) -> FramePacket:
        self.sequence += 1
        return FramePacket(
            frame={"sequence": self.sequence},
            timestamp=datetime.now(UTC),
            source_id=self.source_id,
            source_uri=self.safe_uri,
            capture_fps=15.0,
            measured_fps=14.5,
            sequence=self.sequence,
        )


def test_validation_is_bounded_by_max_frames() -> None:
    report = validate_rtsp_source(
        FakeSource(),
        duration_seconds=None,
        max_frames=3,
        clock=StepClock(),
    )

    assert report.frames_read == 3
    assert report.first_sequence == 1
    assert report.last_sequence == 3
    assert report.capture_fps == 15.0
    assert report.measured_fps == 14.5
    assert report.source_uri == "rtsp://***:***@192.0.2.10:554/stream1"
    assert report.observed_read_fps is not None


def test_validation_can_save_first_snapshot(tmp_path: Path) -> None:
    writes: list[tuple[object, Path]] = []

    def writer(frame: object, path: Path) -> None:
        writes.append((frame, path))

    snapshot = tmp_path / "first-frame.jpg"
    report = validate_rtsp_source(
        FakeSource(),
        duration_seconds=None,
        max_frames=2,
        snapshot_path=snapshot,
        snapshot_writer=writer,
        clock=StepClock(),
    )

    assert writes == [({"sequence": 1}, snapshot)]
    assert report.snapshot_path == str(snapshot)


def test_validation_requires_a_bound() -> None:
    with pytest.raises(ValueError, match="must bound validation"):
        validate_rtsp_source(FakeSource(), duration_seconds=None, max_frames=None)


def test_validation_rejects_invalid_max_frames() -> None:
    with pytest.raises(ValueError, match="max_frames"):
        validate_rtsp_source(FakeSource(), max_frames=0)
