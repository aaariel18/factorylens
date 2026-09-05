from __future__ import annotations

import os

from factorylens.sources import RTSPSource
from factorylens.vision import GestureTriggerConfig, NormalizedROI, ThreeFingerGestureTrigger
from factorylens.vision.mediapipe_hands import MediaPipeHandsDetector


uri = os.environ["FACTORYLENS_RTSP_URL"]
source = RTSPSource(uri, source_id="cnc-03-spindle")
detector = MediaPipeHandsDetector(count_thumb=False)
trigger = ThreeFingerGestureTrigger(
    "cnc-03",
    config=GestureTriggerConfig(
        hold_seconds=1.5,
        cooldown_seconds=10.0,
        min_confidence=0.65,
        sample_every_n_frames=3,
        # Start broad, then tighten this ROI using frames from the real installation.
        roi=NormalizedROI(x=0.45, y=0.15, width=0.5, height=0.75),
    ),
)

try:
    with source, detector:
        for packet in source.frames():
            observation = None
            if packet.sequence % trigger.config.sample_every_n_frames == 0:
                observation = detector.detect(
                    packet.frame,
                    timestamp=packet.timestamp,
                    source_id=packet.source_id,
                )

            result = trigger.process(observation, frame_sequence=packet.sequence)
            if result.triggered and result.event is not None:
                print(result.event.to_json())
                break
finally:
    source.close()
    detector.close()
