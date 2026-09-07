import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import factorylens.cycle
import factorylens.events
import factorylens.evidence
import factorylens.session
import factorylens.simulation
import factorylens.sources.rtsp
import factorylens.workflow

BASE = datetime(2026, 9, 7, 2, 0, tzinfo=UTC)


class FakeVideoSink:
    def __init__(self) -> None:
        self.frames: list[Any] = []
        self.closed = False

    def write(self, frame: Any) -> None:
        self.frames.append(frame)

    def close(self) -> None:
        self.closed = True


class FakeBackend:
    def __init__(self) -> None:
        self.sink = FakeVideoSink()
        self.snapshots: list[Path] = []
        self.opened_video: Path | None = None
        self.opened_fps: float | None = None

    def save_image(self, path: Path, frame: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(frame), encoding="utf-8")
        self.snapshots.append(path)

    def open_video(self, path: Path, *, fps: float, frame: Any) -> FakeVideoSink:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fake-mp4")
        self.opened_video = path
        self.opened_fps = fps
        return self.sink


def packet(seconds: float, sequence: int, frame: str) -> factorylens.sources.rtsp.FramePacket:
    return factorylens.sources.rtsp.FramePacket(
        frame=frame,
        timestamp=BASE + timedelta(seconds=seconds),
        source_id="cnc-03-spindle",
        source_uri="rtsp://***:***@camera/stream1",
        capture_fps=20.0,
        measured_fps=19.5,
        sequence=sequence,
    )


def test_evidence_recorder_keeps_pre_roll_snapshots_and_manifest(tmp_path: Path) -> None:
    backend = FakeBackend()
    recorder = factorylens.evidence.JobEvidenceRecorder(
        "cnc-03",
        machine_type="cnc_milling",
        job={"material": "S45C", "process": "finishing"},
        config=factorylens.evidence.EvidenceRecorderConfig(
            root_dir=tmp_path,
            pre_roll_seconds=5.0,
            snapshot_offsets_seconds=(0.0, 2.0, 10.0),
        ),
        backend=backend,
    )

    recorder.ingest(packet(-7.0, 1, "too-old"))
    recorder.ingest(packet(-4.0, 2, "pre-4"))
    recorder.ingest(packet(-1.0, 3, "pre-1"))

    session = factorylens.session.MachineSession("cnc-03", "cnc_milling")
    session.trigger_operator_note()
    session.set_job_context(material="S45C", process="finishing")
    started = session.machine_started(timestamp=BASE, trigger_source="plc-run")

    start_events = recorder.start_cycle(started)
    recorder.ingest(packet(2.1, 4, "after-2"))
    recorder.ingest(packet(10.1, 5, "after-10"))
    finished = session.machine_finished(
        timestamp=BASE + timedelta(seconds=11),
        trigger_source="plc-run",
    )
    result = recorder.finish_cycle(finished)

    assert [event.event_type for event in start_events] == [
        factorylens.events.EventType.VIDEO_RECORDING_STARTED,
        factorylens.events.EventType.SNAPSHOT_CAPTURED,
    ]
    assert backend.sink.frames[:2] == ["pre-4", "pre-1"]
    assert len(backend.snapshots) == 3
    assert backend.sink.closed is True
    assert result.manifest_path.exists()
    assert result.video_path.exists()

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    event_types = [item["event"]["type"] for item in manifest["events"]]
    assert event_types.count("snapshot_captured") == 3
    assert "video_recording_started" in event_types
    assert "video_recording_finished" in event_types
    assert manifest["job"] == {"material": "S45C", "process": "finishing"}


def test_workflow_connects_armed_session_cycle_and_evidence(tmp_path: Path) -> None:
    session = factorylens.session.MachineSession("cnc-03", "cnc_milling")
    session.trigger_operator_note()
    context = session.set_job_context(material="S45C", process="finishing")

    trigger = factorylens.cycle.DebouncedCycleTrigger(
        "cnc-03",
        machine_type="cnc_milling",
        config=factorylens.cycle.CycleTriggerConfig(
            start_stability_seconds=0.0,
            stop_stability_seconds=0.0,
        ),
    )
    backend = FakeBackend()
    recorder = factorylens.evidence.JobEvidenceRecorder(
        "cnc-03",
        machine_type="cnc_milling",
        config=factorylens.evidence.EvidenceRecorderConfig(
            root_dir=tmp_path,
            snapshot_offsets_seconds=(0.0,),
        ),
        backend=backend,
    )
    workflow = factorylens.workflow.CNCWorkflow(session, trigger, recorder)
    workflow.attach_event(context)
    workflow.ingest_frame(packet(-1.0, 1, "pre-roll"))

    signal = factorylens.simulation.SimulatedMachineSignal("simulated-run-bit")
    started = workflow.process_machine_state(signal.observe(True, timestamp=BASE))

    assert started.reason == "cycle_started"
    assert session.state is factorylens.session.SessionState.RECORDING
    assert recorder.active is True
    assert started.events[0].data["signal_class"] == "simulated"

    workflow.ingest_frame(packet(1.0, 2, "running"))
    finished = workflow.process_machine_state(
        signal.observe(False, timestamp=BASE + timedelta(seconds=2)),
    )

    assert finished.reason == "cycle_finished"
    assert finished.evidence is not None
    assert finished.evidence.manifest_path.exists()
    assert session.state is factorylens.session.SessionState.COMPLETE
    assert recorder.active is False
