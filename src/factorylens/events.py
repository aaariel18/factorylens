from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class EventType(StrEnum):
    GESTURE_TRIGGERED = "gesture_triggered"
    OPERATOR_NOTE_STARTED = "operator_note_started"
    OPERATOR_NOTE_CAPTURED = "operator_note_captured"
    JOB_CONTEXT_SET = "job_context_set"
    MACHINE_CYCLE_STARTED = "machine_cycle_started"
    MACHINE_CYCLE_FINISHED = "machine_cycle_finished"
    SNAPSHOT_CAPTURED = "snapshot_captured"
    VIDEO_RECORDING_STARTED = "video_recording_started"
    VIDEO_RECORDING_FINISHED = "video_recording_finished"
    ANOMALY_DETECTED = "anomaly_detected"
    EVIDENCE_CAPTURED = "evidence_captured"


@dataclass(frozen=True, slots=True)
class Evidence:
    kind: str
    uri: str
    media_type: str | None = None
    sha256: str | None = None


@dataclass(frozen=True, slots=True)
class MachineEvent:
    event_type: EventType
    machine_id: str
    machine_type: str = "unknown"
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    job: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    evidence: tuple[Evidence, ...] = ()
    schema_version: str = "0.1"

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["timestamp"] = self.timestamp.isoformat()
        payload["event"] = {
            "type": payload.pop("event_type"),
            "timestamp": payload.pop("timestamp"),
        }
        payload["machine"] = {
            "id": payload.pop("machine_id"),
            "type": payload.pop("machine_type"),
        }
        return payload

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def write_json(self, path: str | Path) -> Path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(self.to_json() + "\n", encoding="utf-8")
        return output
