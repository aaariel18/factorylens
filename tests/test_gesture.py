from __future__ import annotations

from datetime import UTC, datetime, timedelta

from factorylens.events import EventType
from factorylens.vision import (
    GestureTriggerConfig,
    HandGestureObservation,
    NormalizedROI,
    ThreeFingerGestureTrigger,
)


BASE = datetime(2026, 9, 5, 7, 0, tzinfo=UTC)


def observation(
    seconds: float,
    *,
    fingers: int = 3,
    confidence: float = 0.9,
    x: float = 0.5,
    y: float = 0.5,
) -> HandGestureObservation:
    return HandGestureObservation(
        finger_count=fingers,
        confidence=confidence,
        center_x=x,
        center_y=y,
        timestamp=BASE + timedelta(seconds=seconds),
        source_id="cnc-03-spindle",
    )


def test_three_fingers_must_be_held_before_triggering() -> None:
    trigger = ThreeFingerGestureTrigger(
        "cnc-03",
        config=GestureTriggerConfig(hold_seconds=1.5, sample_every_n_frames=1),
    )

    first = trigger.process(observation(0.0), frame_sequence=0)
    middle = trigger.process(observation(1.0), frame_sequence=1)
    fired = trigger.process(observation(1.6), frame_sequence=2)

    assert first.reason == "holding"
    assert middle.triggered is False
    assert 0.6 < middle.hold_progress < 0.7
    assert fired.triggered is True
    assert fired.event is not None
    assert fired.event.event_type is EventType.GESTURE_TRIGGERED
    assert fired.event.data["gesture"] == "three_fingers"
    assert fired.event.data["source_id"] == "cnc-03-spindle"


def test_trigger_requires_release_before_another_gesture() -> None:
    trigger = ThreeFingerGestureTrigger(
        "cnc-03",
        config=GestureTriggerConfig(
            hold_seconds=1.0,
            cooldown_seconds=5.0,
            sample_every_n_frames=1,
        ),
    )

    trigger.process(observation(0.0), frame_sequence=0)
    fired = trigger.process(observation(1.1), frame_sequence=1)
    latched = trigger.process(observation(1.5), frame_sequence=2)

    assert fired.triggered is True
    assert latched.reason == "awaiting_gesture_release"

    released = trigger.process(observation(2.0, fingers=0), frame_sequence=3)
    trigger.process(observation(2.1), frame_sequence=4)
    cooldown = trigger.process(observation(3.2), frame_sequence=5)
    later = trigger.process(observation(6.2), frame_sequence=6)

    assert released.reason == "finger_count_mismatch"
    assert cooldown.reason == "cooldown"
    assert later.triggered is True


def test_roi_and_confidence_filter_false_triggers() -> None:
    trigger = ThreeFingerGestureTrigger(
        "cnc-03",
        config=GestureTriggerConfig(
            hold_seconds=0.0,
            min_confidence=0.7,
            sample_every_n_frames=1,
            roi=NormalizedROI(x=0.25, y=0.25, width=0.5, height=0.5),
        ),
    )

    outside = trigger.process(observation(0.0, x=0.9), frame_sequence=0)
    low_confidence = trigger.process(
        observation(0.1, confidence=0.4),
        frame_sequence=1,
    )
    valid = trigger.process(observation(0.2), frame_sequence=2)

    assert outside.reason == "outside_roi"
    assert low_confidence.reason == "low_confidence"
    assert valid.triggered is True


def test_sampling_skips_frames_without_advancing_hold() -> None:
    trigger = ThreeFingerGestureTrigger(
        "cnc-03",
        config=GestureTriggerConfig(hold_seconds=1.0, sample_every_n_frames=2),
    )

    skipped = trigger.process(observation(0.0), frame_sequence=1)
    sampled = trigger.process(observation(0.1), frame_sequence=2)
    skipped_again = trigger.process(observation(1.2), frame_sequence=3)
    fired = trigger.process(observation(1.3), frame_sequence=4)

    assert skipped.sampled is False
    assert sampled.reason == "holding"
    assert skipped_again.reason == "frame_skipped"
    assert fired.triggered is True
