# Three-Finger Operator Trigger

FactoryLens uses a deliberate hand gesture as the first **human-to-machine metadata** trigger. The initial code is three fingers held steadily in a configured region of interest (ROI).

The gesture is not a safety signal and must never start, stop or override CNC motion. Its job is only to request the next FactoryLens action, such as opening an operator voice-note session.

## Why hold + ROI + cooldown?

A single detected frame is too easy to trigger accidentally in a workshop. FactoryLens therefore applies several gates:

1. **ROI** — the hand must appear in the operator gesture zone, not anywhere in the machine view.
2. **Confidence** — weak hand observations are ignored.
3. **Target count** — the initial code requires three visible fingers.
4. **Hold duration** — the pose must remain valid for about 1.5 seconds.
5. **Frame sampling** — gesture inference can run every few frames to reduce CPU load.
6. **Release latch** — after a successful trigger, the operator must release/change the gesture before another trigger is allowed.
7. **Cooldown** — a second deliberate gesture cannot trigger immediately after the first one.

These controls reduce false activations before any model-specific tuning is added.

## Install the optional hand-landmark adapter

```bash
python -m pip install -e ".[camera,gesture]"
```

The FactoryLens trigger state machine itself has no MediaPipe dependency. `MediaPipeHandsDetector` is only one replaceable adapter that converts a camera frame into `HandGestureObservation`.

## Standard pose for the first prototype

For the first CNC field test, use one repeatable pose:

- palm approximately facing the camera;
- index, middle and ring fingers extended;
- pinky folded;
- thumb position is ignored by the default detector;
- keep the hand inside the configured gesture ROI;
- hold the pose steadily for at least 1.5 seconds.

Ignoring the thumb by default makes the first prototype less sensitive to left/right handedness and camera mirroring. This can be changed later if a different gesture vocabulary is needed.

## Detector-independent trigger

```python
from datetime import UTC, datetime

from factorylens.vision import (
    GestureTriggerConfig,
    HandGestureObservation,
    NormalizedROI,
    ThreeFingerGestureTrigger,
)

trigger = ThreeFingerGestureTrigger(
    "cnc-03",
    config=GestureTriggerConfig(
        hold_seconds=1.5,
        cooldown_seconds=10.0,
        min_confidence=0.65,
        sample_every_n_frames=3,
        roi=NormalizedROI(x=0.45, y=0.15, width=0.50, height=0.75),
    ),
)

observation = HandGestureObservation(
    finger_count=3,
    confidence=0.92,
    center_x=0.70,
    center_y=0.45,
    timestamp=datetime.now(UTC),
    source_id="cnc-03-spindle",
)

result = trigger.process(observation, frame_sequence=30)
if result.triggered:
    print(result.event.to_json())
```

## Real RTSP example

After `FACTORYLENS_RTSP_URL` is configured locally:

```bash
python examples/cnc/gesture_trigger_demo.py
```

The demo connects:

```text
RTSPSource
   ↓ sampled frames
MediaPipeHandsDetector
   ↓ HandGestureObservation
ThreeFingerGestureTrigger
   ↓
gesture_triggered MachineEvent
```

A later workflow will consume that event to start the 120-second maximum operator voice-note capture.

## Field calibration on the CNC installation

The ROI values in the example are placeholders. They are not measurements from the real camera image.

Use a snapshot from `factorylens validate-rtsp` and define a gesture zone that is:

- clearly visible to the operator;
- away from spindle/tool motion;
- away from coolant spray where possible;
- large enough for normal operator height/reach variation;
- small enough that hands inside the work area do not trigger the operator command.

Then test at least these conditions:

- bare hand and the actual gloves used in production;
- bright and dim machine lighting;
- wet/coolant-reflective background;
- machine idle and spindle running;
- operator at slightly different distances/angles;
- deliberate 3-finger pose vs normal pointing, grabbing and tool-loading motions.

Record false positives and false negatives. Do not claim production-ready gesture accuracy until those tests are complete.

## CPU guidance

The trigger supports `sample_every_n_frames` so hand inference does not need to run at full camera FPS. Start at every 3rd frame. If six cameras are eventually active, benchmark the total CPU budget before increasing the gesture sampling rate.

## Safety boundary

This gesture is **operator metadata input only**. It must not be wired directly to CNC cycle start, spindle commands, door interlocks, emergency stops or any certified safety function.
