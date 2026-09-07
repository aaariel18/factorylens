from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from .events import EventType, MachineEvent


class MachineSignalKind(StrEnum):
    """Origin of a machine running/stopped observation."""

    CONTROLLER = "controller"
    DIGITAL_IO = "digital_io"
    MODBUS = "modbus"
    OPC_UA = "opc_ua"
    GPIO = "gpio"
    VISUAL = "visual"
    SIMULATED = "simulated"

    @property
    def signal_class(self) -> str:
        if self is MachineSignalKind.VISUAL:
            return "inferred"
        if self is MachineSignalKind.SIMULATED:
            return "simulated"
        return "measured"


@dataclass(frozen=True, slots=True)
class MachineStateObservation:
    running: bool
    timestamp: datetime
    source_id: str
    kind: MachineSignalKind
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not self.source_id.strip():
            raise ValueError("source_id must not be empty")


@dataclass(frozen=True, slots=True)
class CycleTriggerConfig:
    start_stability_seconds: float = 0.5
    stop_stability_seconds: float = 0.5
    min_confidence: float = 0.5

    def __post_init__(self) -> None:
        if self.start_stability_seconds < 0:
            raise ValueError("start_stability_seconds must be >= 0")
        if self.stop_stability_seconds < 0:
            raise ValueError("stop_stability_seconds must be >= 0")
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError("min_confidence must be between 0 and 1")


@dataclass(frozen=True, slots=True)
class CycleTriggerResult:
    event: MachineEvent | None
    stable_running: bool
    candidate_running: bool | None
    stability_seconds: float
    reason: str


class DebouncedCycleTrigger:
    """Turn noisy machine-state observations into stable cycle start/finish events.

    FactoryLens deliberately treats the signal origin as metadata. Controller/PLC-style
    observations are marked measured, while camera-derived state is marked inferred.
    Neither category is a machine-safety signal.
    """

    def __init__(
        self,
        machine_id: str,
        *,
        machine_type: str = "unknown",
        config: CycleTriggerConfig | None = None,
        initial_running: bool = False,
    ) -> None:
        if not machine_id.strip():
            raise ValueError("machine_id must not be empty")
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.config = config or CycleTriggerConfig()
        self._stable_running = initial_running
        self._candidate_running: bool | None = None
        self._candidate_since: datetime | None = None

    @property
    def stable_running(self) -> bool:
        return self._stable_running

    def _required_stability(self, running: bool) -> float:
        if running:
            return self.config.start_stability_seconds
        return self.config.stop_stability_seconds

    def _event(self, observation: MachineStateObservation, stable_seconds: float) -> MachineEvent:
        event_type = (
            EventType.MACHINE_CYCLE_STARTED
            if observation.running
            else EventType.MACHINE_CYCLE_FINISHED
        )
        return MachineEvent(
            event_type=event_type,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            timestamp=observation.timestamp,
            data={
                "trigger_source": observation.source_id,
                "signal_kind": observation.kind.value,
                "signal_class": observation.kind.signal_class,
                "confidence": observation.confidence,
                "debounce_seconds": stable_seconds,
            },
        )

    def process(self, observation: MachineStateObservation) -> CycleTriggerResult:
        if observation.confidence < self.config.min_confidence:
            self._candidate_running = None
            self._candidate_since = None
            return CycleTriggerResult(
                event=None,
                stable_running=self._stable_running,
                candidate_running=None,
                stability_seconds=0.0,
                reason="low_confidence",
            )

        if observation.running == self._stable_running:
            self._candidate_running = None
            self._candidate_since = None
            return CycleTriggerResult(
                event=None,
                stable_running=self._stable_running,
                candidate_running=None,
                stability_seconds=0.0,
                reason="stable_state_unchanged",
            )

        if self._candidate_running != observation.running or self._candidate_since is None:
            self._candidate_running = observation.running
            self._candidate_since = observation.timestamp

        stability_seconds = max(
            (observation.timestamp - self._candidate_since).total_seconds(),
            0.0,
        )
        required = self._required_stability(observation.running)
        if stability_seconds < required:
            return CycleTriggerResult(
                event=None,
                stable_running=self._stable_running,
                candidate_running=self._candidate_running,
                stability_seconds=stability_seconds,
                reason="debouncing",
            )

        self._stable_running = observation.running
        event = self._event(observation, stability_seconds)
        self._candidate_running = None
        self._candidate_since = None
        return CycleTriggerResult(
            event=event,
            stable_running=self._stable_running,
            candidate_running=None,
            stability_seconds=stability_seconds,
            reason="cycle_started" if observation.running else "cycle_finished",
        )
