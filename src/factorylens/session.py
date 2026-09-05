from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from .events import EventType, MachineEvent


class SessionState(StrEnum):
    IDLE = "idle"
    LISTENING = "listening"
    ARMED = "armed"
    RECORDING = "recording"
    COMPLETE = "complete"


@dataclass(slots=True)
class MachineSession:
    machine_id: str
    machine_type: str = "unknown"
    state: SessionState = SessionState.IDLE
    job: dict[str, str] = field(default_factory=dict)

    def _event(self, event_type: EventType, **data: object) -> MachineEvent:
        return MachineEvent(
            event_type=event_type,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            job=dict(self.job),
            data=dict(data),
        )

    def trigger_operator_note(self, gesture: str = "three_fingers") -> list[MachineEvent]:
        if self.state not in {SessionState.IDLE, SessionState.COMPLETE}:
            raise RuntimeError(f"cannot start operator note while session is {self.state}")
        self.job.clear()
        self.state = SessionState.LISTENING
        return [
            self._event(EventType.GESTURE_TRIGGERED, gesture=gesture),
            self._event(EventType.OPERATOR_NOTE_STARTED),
        ]

    def set_job_context(self, *, material: str, process: str) -> MachineEvent:
        if self.state != SessionState.LISTENING:
            raise RuntimeError("job context can only be set after operator-note capture starts")
        material = material.strip()
        process = process.strip()
        if not material or not process:
            raise ValueError("material and process are required")
        self.job.update(material=material, process=process)
        self.state = SessionState.ARMED
        return self._event(EventType.JOB_CONTEXT_SET)

    def machine_started(self) -> MachineEvent:
        if self.state != SessionState.ARMED:
            raise RuntimeError("machine can only start after job context is armed")
        self.state = SessionState.RECORDING
        return self._event(EventType.MACHINE_CYCLE_STARTED)

    def machine_finished(self) -> MachineEvent:
        if self.state != SessionState.RECORDING:
            raise RuntimeError("machine can only finish while a cycle is recording")
        self.state = SessionState.COMPLETE
        return self._event(EventType.MACHINE_CYCLE_FINISHED)
