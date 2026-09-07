from __future__ import annotations

import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Callable

from .events import EventType, Evidence, MachineEvent
from .session import MachineSession
from .speech import JobContextNormalizer, Transcript

Sleeper = Callable[[float], None]


@dataclass(frozen=True, slots=True)
class DemoStep:
    at_seconds: float
    label: str
    detail: str
    event: MachineEvent | None = None


@dataclass(frozen=True, slots=True)
class PrelaunchDemoResult:
    timeline_path: Path
    manifest_path: Path
    steps: tuple[DemoStep, ...]


def _event(
    event_type: EventType,
    *,
    timestamp: datetime,
    job: dict[str, str],
    data: dict[str, object] | None = None,
    evidence: tuple[Evidence, ...] = (),
) -> MachineEvent:
    return MachineEvent(
        event_type=event_type,
        machine_id="cnc-demo-01",
        machine_type="cnc_milling",
        timestamp=timestamp,
        job=dict(job),
        data={"signal_class": "simulated", **(data or {})},
        evidence=evidence,
    )


def build_prelaunch_demo(*, started_at: datetime | None = None) -> tuple[DemoStep, ...]:
    """Build a deterministic, hardware-free FactoryLens story for public demos.

    Every machine-state transition is explicitly marked simulated. This function exists so
    the project can be demonstrated before field hardware arrives without presenting the
    result as real CNC validation.
    """

    base = started_at or datetime.now(UTC)
    session = MachineSession("cnc-demo-01", "cnc_milling")
    gesture, note_started = session.trigger_operator_note()

    transcript = Transcript(
        text="bahan es empat lima ce proses penghalusan",
        language="id",
        confidence=0.94,
    )
    normalized = JobContextNormalizer().normalize(transcript)
    if not normalized.ready or normalized.material is None or normalized.process is None:
        raise RuntimeError("prelaunch demo transcript unexpectedly failed normalization")

    context = session.set_job_context(
        material=normalized.material,
        process=normalized.process,
    )
    job = dict(session.job)

    machine_start = session.machine_started(
        timestamp=base + timedelta(seconds=17),
        trigger_source="simulated-run-bit",
        signal_kind="simulated",
        signal_class="simulated",
        confidence=1.0,
        debounce_seconds=0.5,
    )
    machine_stop = session.machine_finished(
        timestamp=base + timedelta(seconds=41),
        trigger_source="simulated-run-bit",
        signal_kind="simulated",
        signal_class="simulated",
        confidence=1.0,
        debounce_seconds=0.5,
    )

    video_path = "data/prelaunch-demo/cycle.mp4"
    snapshot0 = "data/prelaunch-demo/start_000s.jpg"
    snapshot2 = "data/prelaunch-demo/start_002s.jpg"
    snapshot10 = "data/prelaunch-demo/start_010s.jpg"

    steps = (
        DemoStep(0, "SIMULATION", "No camera or CNC required. Machine signals are simulated."),
        DemoStep(2, "GESTURE", "Three-finger operator trigger detected.", gesture),
        DemoStep(5, "AUDIO", "Operator voice-note capture starts.", note_started),
        DemoStep(9, "TRANSCRIPT", '"bahan es empat lima ce proses penghalusan"'),
        DemoStep(12, "JOB CONTEXT", "Material=S45C • Process=finishing", context),
        DemoStep(17, "MACHINE START", "Simulated CNC RUN becomes stable.", machine_start),
        DemoStep(
            18,
            "VIDEO",
            "Black-box recording starts with a 5 s pre-roll target.",
            _event(
                EventType.VIDEO_RECORDING_STARTED,
                timestamp=base + timedelta(seconds=18),
                job=job,
                data={"pre_roll_seconds": 5.0},
                evidence=(Evidence(kind="video", uri=video_path, media_type="video/mp4"),),
            ),
        ),
        DemoStep(
            19,
            "SNAPSHOT",
            "Cycle-start evidence captured at T+0 s.",
            _event(
                EventType.SNAPSHOT_CAPTURED,
                timestamp=base + timedelta(seconds=19),
                job=job,
                data={"offset_seconds": 0.0},
                evidence=(Evidence(kind="snapshot", uri=snapshot0, media_type="image/jpeg"),),
            ),
        ),
        DemoStep(
            23,
            "SNAPSHOT",
            "Second evidence frame captured at T+2 s.",
            _event(
                EventType.SNAPSHOT_CAPTURED,
                timestamp=base + timedelta(seconds=23),
                job=job,
                data={"offset_seconds": 2.0},
                evidence=(Evidence(kind="snapshot", uri=snapshot2, media_type="image/jpeg"),),
            ),
        ),
        DemoStep(
            31,
            "SNAPSHOT",
            "Third evidence frame captured at T+10 s.",
            _event(
                EventType.SNAPSHOT_CAPTURED,
                timestamp=base + timedelta(seconds=31),
                job=job,
                data={"offset_seconds": 10.0},
                evidence=(Evidence(kind="snapshot", uri=snapshot10, media_type="image/jpeg"),),
            ),
        ),
        DemoStep(41, "MACHINE STOP", "Simulated CNC RUN turns off.", machine_stop),
        DemoStep(
            42,
            "VIDEO",
            "Cycle recording closes and the job manifest is finalized.",
            _event(
                EventType.VIDEO_RECORDING_FINISHED,
                timestamp=base + timedelta(seconds=42),
                job=job,
                evidence=(Evidence(kind="video", uri=video_path, media_type="video/mp4"),),
            ),
        ),
        DemoStep(45, "JOB BUNDLE", "One timeline now links context, machine state and evidence."),
    )
    return steps


def run_prelaunch_demo(
    *,
    output_dir: Path = Path("data/prelaunch-demo"),
    duration_seconds: float = 45.0,
    realtime: bool = False,
    sleeper: Sleeper = time.sleep,
) -> PrelaunchDemoResult:
    if duration_seconds <= 0:
        raise ValueError("duration_seconds must be > 0")

    steps = build_prelaunch_demo()
    output_dir.mkdir(parents=True, exist_ok=True)
    timeline_path = output_dir / "timeline.jsonl"
    manifest_path = output_dir / "manifest.json"

    scale = duration_seconds / max(step.at_seconds for step in steps)
    previous = 0.0
    event_payloads: list[dict[str, object]] = []

    with timeline_path.open("w", encoding="utf-8") as timeline:
        for step in steps:
            if realtime:
                sleeper(max((step.at_seconds - previous) * scale, 0.0))
            previous = step.at_seconds

            marker = f"[{step.at_seconds:05.1f}s] {step.label:<13} {step.detail}"
            print(marker, flush=True)
            payload: dict[str, object] = {
                "at_seconds": step.at_seconds,
                "label": step.label,
                "detail": step.detail,
            }
            if step.event is not None:
                payload["event"] = step.event.to_dict()
                event_payloads.append(step.event.to_dict())
            timeline.write(json.dumps(payload, ensure_ascii=False) + "\n")

    manifest = {
        "demo": "FactoryLens pre-launch simulation",
        "simulation": True,
        "field_validated": False,
        "duration_seconds": duration_seconds,
        "machine": {"id": "cnc-demo-01", "type": "cnc_milling"},
        "job": {"material": "S45C", "process": "finishing"},
        "events": event_payloads,
        "notice": "Machine-state and evidence media paths in this demo are simulated.",
    }
    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return PrelaunchDemoResult(timeline_path, manifest_path, steps)
