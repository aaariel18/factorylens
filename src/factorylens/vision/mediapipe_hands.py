from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Self

from .gesture import HandGestureObservation


class MediaPipeHandsDetector:
    """Optional MediaPipe adapter that converts a frame into a hand observation.

    MediaPipe is imported lazily so the FactoryLens core stays dependency-light. By default
    the thumb is ignored when counting fingers because thumb extension is more sensitive to
    handedness, camera mirroring and hand rotation. For the initial FactoryLens code gesture,
    operators should extend index/middle/ring and fold the pinky.
    """

    def __init__(
        self,
        *,
        max_num_hands: int = 1,
        min_detection_confidence: float = 0.65,
        min_tracking_confidence: float = 0.65,
        count_thumb: bool = False,
    ) -> None:
        try:
            import mediapipe as mp
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "MediaPipe is required for hand landmarks. Install FactoryLens with the "
                "gesture extra: python -m pip install -e '.[gesture]'"
            ) from exc

        if not hasattr(mp, "solutions") or not hasattr(mp.solutions, "hands"):
            raise RuntimeError(
                "This MediaPipe build does not expose mediapipe.solutions.hands. "
                "Use a compatible MediaPipe build or provide another hand detector adapter."
            )

        self.count_thumb = count_thumb
        self._hands = mp.solutions.hands.Hands(
            static_image_mode=False,
            max_num_hands=max_num_hands,
            min_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )

    @staticmethod
    def _finger_is_extended(landmarks: Any, tip: int, pip: int) -> bool:
        return landmarks[tip].y < landmarks[pip].y

    @staticmethod
    def _thumb_is_extended(landmarks: Any, handedness: str) -> bool:
        if handedness.lower() == "left":
            return landmarks[4].x > landmarks[3].x
        return landmarks[4].x < landmarks[3].x

    def detect(
        self,
        frame: Any,
        *,
        timestamp: datetime | None = None,
        source_id: str = "camera",
    ) -> HandGestureObservation | None:
        if frame is None:
            return None

        # OpenCV frames are normally BGR. Reversing the final channel gives RGB without
        # importing cv2 again in this adapter.
        rgb_frame = frame[..., ::-1]
        result = self._hands.process(rgb_frame)
        if not result.multi_hand_landmarks:
            return None

        hand = result.multi_hand_landmarks[0]
        landmarks = hand.landmark
        classification = None
        if result.multi_handedness:
            classification = result.multi_handedness[0].classification[0]

        handedness = classification.label if classification is not None else "right"
        confidence = float(classification.score) if classification is not None else 1.0

        extended = [
            self._finger_is_extended(landmarks, 8, 6),
            self._finger_is_extended(landmarks, 12, 10),
            self._finger_is_extended(landmarks, 16, 14),
            self._finger_is_extended(landmarks, 20, 18),
        ]
        finger_count = sum(extended)
        if self.count_thumb and self._thumb_is_extended(landmarks, handedness):
            finger_count += 1

        center_x = sum(point.x for point in landmarks) / len(landmarks)
        center_y = sum(point.y for point in landmarks) / len(landmarks)
        return HandGestureObservation(
            finger_count=finger_count,
            confidence=confidence,
            center_x=float(center_x),
            center_y=float(center_y),
            timestamp=timestamp or datetime.now(UTC),
            source_id=source_id,
        )

    def close(self) -> None:
        self._hands.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()
