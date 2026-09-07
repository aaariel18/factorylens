"""FactoryLens core package."""

from .cycle import (
    CycleTriggerConfig,
    DebouncedCycleTrigger,
    MachineSignalKind,
    MachineStateObservation,
)
from .events import EventType, Evidence, MachineEvent
from .evidence import EvidenceRecorderConfig, JobEvidenceRecorder, JobEvidenceResult
from .session import MachineSession, SessionState
from .workflow import CNCWorkflow, WorkflowResult

__all__ = [
    "CNCWorkflow",
    "CycleTriggerConfig",
    "DebouncedCycleTrigger",
    "EventType",
    "Evidence",
    "EvidenceRecorderConfig",
    "JobEvidenceRecorder",
    "JobEvidenceResult",
    "MachineEvent",
    "MachineSession",
    "MachineSignalKind",
    "MachineStateObservation",
    "SessionState",
    "WorkflowResult",
]

__version__ = "0.1.0"
