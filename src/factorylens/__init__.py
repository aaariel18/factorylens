"""FactoryLens core package."""

from .events import EventType, Evidence, MachineEvent
from .session import MachineSession, SessionState

__all__ = ["EventType", "Evidence", "MachineEvent", "MachineSession", "SessionState"]

__version__ = "0.1.0"
