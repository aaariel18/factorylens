from __future__ import annotations

from dataclasses import dataclass

from .cycle import CycleTriggerResult, DebouncedCycleTrigger, MachineStateObservation
from .events import EventType, MachineEvent
from .evidence import JobEvidenceRecorder, JobEvidenceResult
from .session import MachineSession, SessionState
from .sources.rtsp import FramePacket


@dataclass(frozen=True, slots=True)
class WorkflowResult:
    events: tuple[MachineEvent, ...] = ()
    evidence: JobEvidenceResult | None = None
    trigger: CycleTriggerResult | None = None
    reason: str = "no_event"


class CNCWorkflow:
    """Small coordinator for the v0.1 human-context -> machine-cycle -> evidence story."""

    def __init__(
        self,
        session: MachineSession,
        cycle_trigger: DebouncedCycleTrigger,
        evidence_recorder: JobEvidenceRecorder,
    ) -> None:
        if session.machine_id != cycle_trigger.machine_id:
            raise ValueError("session and cycle trigger must use the same machine_id")
        if session.machine_id != evidence_recorder.machine_id:
            raise ValueError("session and evidence recorder must use the same machine_id")
        self.session = session
        self.cycle_trigger = cycle_trigger
        self.evidence_recorder = evidence_recorder

    def attach_event(self, event: MachineEvent) -> None:
        """Attach operator/audio/transcript events to the next job manifest."""
        self.evidence_recorder.attach_event(event)

    def ingest_frame(self, packet: FramePacket) -> tuple[MachineEvent, ...]:
        return self.evidence_recorder.ingest(packet)

    def process_machine_state(self, observation: MachineStateObservation) -> WorkflowResult:
        trigger = self.cycle_trigger.process(observation)
        if trigger.event is None:
            return WorkflowResult(trigger=trigger, reason=trigger.reason)

        metadata = dict(trigger.event.data)
        if trigger.event.event_type is EventType.MACHINE_CYCLE_STARTED:
            if self.session.state is not SessionState.ARMED:
                return WorkflowResult(
                    trigger=trigger,
                    reason="cycle_start_ignored_session_not_armed",
                )
            cycle_event = self.session.machine_started(
                timestamp=trigger.event.timestamp,
                **metadata,
            )
            emitted = self.evidence_recorder.start_cycle(cycle_event)
            return WorkflowResult(
                events=(cycle_event, *emitted),
                trigger=trigger,
                reason="cycle_started",
            )

        if trigger.event.event_type is EventType.MACHINE_CYCLE_FINISHED:
            if self.session.state is not SessionState.RECORDING:
                return WorkflowResult(
                    trigger=trigger,
                    reason="cycle_finish_ignored_session_not_recording",
                )
            cycle_event = self.session.machine_finished(
                timestamp=trigger.event.timestamp,
                **metadata,
            )
            evidence = self.evidence_recorder.finish_cycle(cycle_event)
            return WorkflowResult(
                events=(cycle_event, evidence.events[-1]),
                evidence=evidence,
                trigger=trigger,
                reason="cycle_finished",
            )

        raise AssertionError(f"unexpected cycle event: {trigger.event.event_type}")
