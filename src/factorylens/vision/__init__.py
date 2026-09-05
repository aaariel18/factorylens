"""Computer-vision adapters and detector-independent trigger primitives."""

from .gesture import (
    GestureTriggerConfig,
    GestureTriggerResult,
    HandGestureObservation,
    NormalizedROI,
    ThreeFingerGestureTrigger,
)

__all__ = [
    "GestureTriggerConfig",
    "GestureTriggerResult",
    "HandGestureObservation",
    "NormalizedROI",
    "ThreeFingerGestureTrigger",
]
