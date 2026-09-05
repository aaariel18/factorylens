from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..events import EventType, MachineEvent


@dataclass(frozen=True, slots=True)
class NormalizedROI:
    """Region of interest expressed in normalized 0..1 coordinates."""

    x: float = 0.0
    y: float = 0.0
    width: float = 1.0
    height: float = 1.0

    def __post_init__(self) -> None:
        values = (self.x, self.y, self.width, self.height)
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("ROI values must be between 0 and 1")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("ROI width and height must be > 0")
        if self.x + self.width > 1 or self.y + self.height > 1:
            raise ValueError("ROI must fit inside normalized frame bounds")

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height


@dataclass(frozen=True, slots=True)
class HandGestureObservation:
    """Detector-independent hand observation consumed by the trigger state machine."""

    finger_count: int
    confidence: float
    center_x: float
    center_y: float
    timestamp: datetime
    source_id: str = "camera"

    def __post_init__(self) -> None:
        if not 0 <= self.finger_count <= 5:
            raise ValueError("finger_count must be between 0 and 5")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")
        if not 0 <= self.center_x <= 1 or not 0 <= self.center_y <= 1:
            raise ValueError("hand center must use normalized 0..1 coordinates")


@dataclass(frozen=True, slots=True)
class GestureTriggerConfig:
    target_fingers: int = 3
    hold_seconds: float = 1.5
    cooldown_seconds: float = 10.0
    min_confidence: float = 0.65
    sample_every_n_frames: int = 3
    roi: NormalizedROI = NormalizedROI()

    def __post_init__(self) -> None:
        if not 0 <= self.target_fingers <= 5:
            raise ValueError("target_fingers must be between 0 and 5")
        if self.hold_seconds < 0:
            raise ValueError("hold_seconds must be >= 0")
        if self.cooldown_seconds < 0:
            raise ValueError("cooldown_seconds must be >= 0")
        if not 0 <= self.min_confidence <= 1:
            raise ValueError("min_confidence must be between 0 and 1")
        if self.sample_every_n_frames <= 0:
            raise ValueError("sample_every_n_frames must be > 0")


@dataclass(frozen=True, slots=True)
class GestureTriggerResult:
    sampled: bool
    matched: bool
    triggered: bool
    hold_progress: float
    confidence: float | None
    reason: str
    event: MachineEvent | None = None


class ThreeFingerGestureTrigger:
    """Debounced, ROI-aware gesture trigger suitable for CPU-friendly camera pipelines."""

    def __init__(
        self,
        machine_id: str,
        *,
        machine_type: str = "cnc_milling",
        config: GestureTriggerConfig | None = None,
    ) -> None:
        if not machine_id:
            raise ValueError("machine_id must not be empty")
        self.machine_id = machine_id
        self.machine_type = machine_type
        self.config = config or GestureTriggerConfig()
        self._candidate_since: datetime | None = None
        self._last_triggered_at: datetime | None = None
        self._latched = False

    def reset(self) -> None:
        self._candidate_since = None
        self._latched = False

    def _is_match(self, observation: HandGestureObservation) -> tuple[bool, str]:
        if observation.confidence < self.config.min_confidence:
            return False, "low_confidence"
        if not self.config.roi.contains(observation.center_x, observation.center_y):
            return False, "outside_roi"
        if observation.finger_count != self.config.target_fingers:
            return False, "finger_count_mismatch"
        return True, "matched"

    def process(
        self,
        observation: HandGestureObservation | None,
        *,
        frame_sequence: int,
    ) -> GestureTriggerResult:
        if frame_sequence < 0:
            raise ValueError("frame_sequence must be >= 0")
        if frame_sequence % self.config.sample_every_n_frames != 0:
            return GestureTriggerResult(
                sampled=False,
                matched=False,
                triggered=False,
                hold_progress=0.0,
                confidence=observation.confidence if observation else None,
                reason="frame_skipped",
            )

        if observation is None:
            self.reset()
            return GestureTriggerResult(
                sampled=True,
                matched=False,
                triggered=False,
                hold_progress=0.0,
                confidence=None,
                reason="no_hand",
            )

        matched, reason = self._is_match(observation)
        if not matched:
            self.reset()
            return GestureTriggerResult(
                sampled=True,
                matched=False,
                triggered=False,
                hold_progress=0.0,
                confidence=observation.confidence,
                reason=reason,
            )

        if self._latched:
            return GestureTriggerResult(
                sampled=True,
                matched=True,
                triggered=False,
                hold_progress=1.0,
                confidence=observation.confidence,
                reason="awaiting_gesture_release",
            )

        if self._candidate_since is None:
            self._candidate_since = observation.timestamp

        hold_elapsed = max((observation.timestamp - self._candidate_since).total_seconds(), 0.0)
        if self.config.hold_seconds == 0:
            hold_progress = 1.0
        else:
            hold_progress = min(hold_elapsed / self.config.hold_seconds, 1.0)

        if hold_elapsed < self.config.hold_seconds:
            return GestureTriggerResult(
                sampled=True,
                matched=True,
                triggered=False,
                hold_progress=hold_progress,
                confidence=observation.confidence,
                reason="holding",
            )

        if self._last_triggered_at is not None:
            since_last = (observation.timestamp - self._last_triggered_at).total_seconds()
            if since_last < self.config.cooldown_seconds:
                return GestureTriggerResult(
                    sampled=True,
                    matched=True,
                    triggered=False,
                    hold_progress=1.0,
                    confidence=observation.confidence,
                    reason="cooldown",
                )

        event = MachineEvent(
            event_type=EventType.GESTURE_TRIGGERED,
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            timestamp=observation.timestamp,
            data={
                "gesture": "three_fingers",
                "finger_count": observation.finger_count,
                "confidence": observation.confidence,
                "hold_seconds": hold_elapsed,
                "source_id": observation.source_id,
                "hand_center": {"x": observation.center_x, "y": observation.center_y},
            },
        )
        self._last_triggered_at = observation.timestamp
        self._candidate_since = None
        self._latched = True
        return GestureTriggerResult(
            sampled=True,
            matched=True,
            triggered=True,
            hold_progress=1.0,
            confidence=observation.confidence,
            reason="triggered",
            event=event,
        )
