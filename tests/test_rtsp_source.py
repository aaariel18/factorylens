from __future__ import annotations

from collections import deque

import pytest

from factorylens.sources.rtsp import RTSPSource, redact_rtsp_uri


class FakeCapture:
    def __init__(self, *, opened=True, frames=None, fps=15.0):
        self.opened = opened
        self.frames = deque(frames or [])
        self.fps = fps
        self.released = False

    def isOpened(self):
        return self.opened and not self.released

    def read(self):
        if not self.frames:
            return False, None
        return self.frames.popleft()

    def get(self, prop_id):
        assert prop_id == 5
        return self.fps

    def release(self):
        self.released = True


class CaptureQueue:
    def __init__(self, *captures):
        self.captures = deque(captures)
        self.uris = []

    def __call__(self, uri):
        self.uris.append(uri)
        return self.captures.popleft()


def test_redact_rtsp_uri_removes_credentials():
    uri = "rtsp://operator:secret@192.168.10.30:554/stream1"
    assert redact_rtsp_uri(uri) == "rtsp://***:***@192.168.10.30:554/stream1"


def test_read_returns_timestamped_packet_without_credentials():
    capture = FakeCapture(frames=[(True, "frame-1")], fps=20.0)
    source = RTSPSource(
        "rtsp://user:password@camera.local:554/stream1",
        source_id="cnc-03-spindle",
        capture_factory=CaptureQueue(capture),
        reconnect_delay_seconds=0,
    )

    packet = source.read()

    assert packet.frame == "frame-1"
    assert packet.sequence == 1
    assert packet.source_id == "cnc-03-spindle"
    assert packet.source_uri == "rtsp://***:***@camera.local:554/stream1"
    assert packet.capture_fps == 20.0
    assert packet.timestamp.tzinfo is not None


def test_read_reconnects_after_transient_failure():
    first = FakeCapture(frames=[(False, None)])
    second = FakeCapture(frames=[(True, "recovered-frame")])
    factory = CaptureQueue(first, second)
    source = RTSPSource(
        "rtsp://camera.local/stream1",
        capture_factory=factory,
        reconnect_delay_seconds=0,
        reconnect_attempts=1,
    )

    packet = source.read()

    assert packet.frame == "recovered-frame"
    assert first.released is True
    assert len(factory.uris) == 2


def test_open_error_never_exposes_password():
    source = RTSPSource(
        "rtsp://operator:super-secret@camera.local/stream1",
        capture_factory=CaptureQueue(FakeCapture(opened=False)),
        reconnect_delay_seconds=0,
    )

    with pytest.raises(ConnectionError) as exc_info:
        source.open()

    message = str(exc_info.value)
    assert "super-secret" not in message
    assert "***:***" in message


def test_frames_respects_max_frames():
    capture = FakeCapture(frames=[(True, 1), (True, 2), (True, 3)])
    source = RTSPSource(
        "rtsp://camera.local/stream1",
        capture_factory=CaptureQueue(capture),
        reconnect_delay_seconds=0,
    )

    packets = list(source.frames(max_frames=2))

    assert [packet.frame for packet in packets] == [1, 2]
