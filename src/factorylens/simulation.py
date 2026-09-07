from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from .cycle import MachineSignalKind, MachineStateObservation


@dataclass(slots=True)
class SimulatedMachineSignal:
    """Test/development signal source that never touches a physical CNC."""

    source_id: str = "simulated-machine"

    def observe(
        self,
        running: bool,
        *,
        timestamp: datetime | None = None,
        confidence: float = 1.0,
    ) -> MachineStateObservation:
        return MachineStateObservation(
            running=running,
            timestamp=timestamp or datetime.now(UTC),
            source_id=self.source_id,
            kind=MachineSignalKind.SIMULATED,
            confidence=confidence,
        )
