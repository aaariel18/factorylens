from __future__ import annotations

import io
from pathlib import Path

import pytest

from factorylens.audio import (
    AudioCaptureConfig,
    AudioCaptureError,
    FFmpegRTSPAudioCapture,
    sanitize_ffmpeg_text,
)
from factorylens.events import EventType


class StepClock:
    def __init__(self, values: list[float]) -> None:
        self.values = iter(values)

    def __call__(self) -> float:
        return next(self.values)


class FakeProcess:
    def __init__(self, stderr_text: str, *, returncode: int = 0) -> None:
        self.stderr = io.StringIO(stderr_text)
        self.returncode: int | None = None
        self.final_returncode = returncode
        self.terminated = False
        self.killed = False

    def poll(self) -> int | None:
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        self.returncode = self.final_returncode
        return self.final_returncode

    def terminate(self) -> None:
        self.terminated = True
        self.returncode = 0

    def kill(self) -> None:
        self.killed = True
        self.returncode = -9


def process_factory_with_file(
    process: FakeProcess,
    output_bytes: bytes = b"RIFFfakewav",
):
    def factory(command, **kwargs):
        Path(command[-1]).write_bytes(output_bytes)
        return process

    return factory


def test_build_command_is_bounded_and_selects_audio(tmp_path: Path) -> None:
    capture = FFmpegRTSPAudioCapture(
        "rtsp://user:secret@192.0.2.10:554/stream1",
        config=AudioCaptureConfig(max_seconds=120, silence_seconds=3),
        ffmpeg_binary="ffmpeg-test",
    )

    command = capture.build_command(tmp_path / "note.wav")

    assert command[0] == "ffmpeg-test"
    assert ["-map", "0:a:0?"] == command[command.index("-map") : command.index("-map") + 2]
    assert command[command.index("-t") + 1] == "120"
    assert "silencedetect=noise=-35.0dB:d=3" in command


def test_capture_stops_after_confirmed_silence_and_emits_event(tmp_path: Path) -> None:
    process = FakeProcess("[silencedetect] silence_start: 12.0\n")
    capture = FFmpegRTSPAudioCapture(
        "rtsp://user:secret@192.0.2.10:554/stream1",
        source_id="cnc-03-spindle",
        config=AudioCaptureConfig(
            max_seconds=120,
            silence_seconds=3,
            start_grace_seconds=10,
        ),
        ffmpeg_binary="ffmpeg-test",
        process_factory=process_factory_with_file(process),
        clock=StepClock([0.0, 15.2]),
    )

    result = capture.capture(tmp_path / "note.wav")
    event = result.to_event("cnc-03")

    assert process.terminated is True
    assert result.stop_reason == "silence"
    assert result.source_uri == "rtsp://***:***@192.0.2.10:554/stream1"
    assert event.event_type is EventType.OPERATOR_NOTE_CAPTURED
    assert event.evidence[0].kind == "audio"
    assert event.evidence[0].media_type == "audio/wav"


def test_capture_uses_max_duration_when_silence_stop_is_disabled(tmp_path: Path) -> None:
    process = FakeProcess("")
    capture = FFmpegRTSPAudioCapture(
        "rtsp://user:secret@192.0.2.10:554/stream1",
        config=AudioCaptureConfig(max_seconds=5, silence_seconds=None),
        ffmpeg_binary="ffmpeg-test",
        process_factory=process_factory_with_file(process),
        clock=StepClock([0.0, 5.0]),
    )

    result = capture.capture(tmp_path / "note.wav")

    assert process.terminated is False
    assert result.stop_reason == "max_duration"


def test_no_audio_stream_is_reported_without_leaking_credentials(tmp_path: Path) -> None:
    process = FakeProcess(
        "Input rtsp://user:secret@192.0.2.10:554/stream1\n"
        "Output file does not contain any stream\n",
        returncode=1,
    )
    capture = FFmpegRTSPAudioCapture(
        "rtsp://user:secret@192.0.2.10:554/stream1",
        ffmpeg_binary="ffmpeg-test",
        process_factory=process_factory_with_file(process, output_bytes=b""),
        clock=StepClock([0.0, 1.0]),
    )

    with pytest.raises(AudioCaptureError) as exc_info:
        capture.capture(tmp_path / "note.wav")

    message = str(exc_info.value)
    assert "usable audio stream" in message
    assert "secret" not in message
    assert "rtsp://***:***@192.0.2.10:554/stream1" in message


def test_ffmpeg_log_sanitizer_redacts_rtsp_credentials() -> None:
    text = "Opening rtsp://alice:camera-pass@10.0.0.4:554/stream1 for reading"
    safe = sanitize_ffmpeg_text(text)

    assert "camera-pass" not in safe
    assert "rtsp://***:***@10.0.0.4:554/stream1" in safe
