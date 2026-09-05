# RTSP Camera Adapter

FactoryLens v0.1 starts with a deliberately small RTSP source adapter. The source layer is responsible for **capture and timing**, not detection or machine-state decisions.

## Install

```bash
python -m pip install -e ".[camera]"
```

For development:

```bash
python -m pip install -e ".[dev,camera]"
```

## Configuration

Keep camera credentials outside the repository:

```bash
export FACTORYLENS_RTSP_URL='rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1'
```

Never commit the real value. The example CNC configuration references the environment variable instead of embedding a URL.

## One-command field validation

Before adding gesture recognition or anomaly models, prove that the physical camera path is stable on the real machine.

Run a 60-second baseline and save one local snapshot:

```bash
factorylens validate-rtsp \
  --source-id cnc-03-spindle \
  --duration 60 \
  --snapshot data/validation/cnc-03-first-frame.jpg \
  --report data/validation/cnc-03-rtsp-report.json
```

The command reads `FACTORYLENS_RTSP_URL` by default. Prefer that environment variable over `--source` so credentials do not end up in shell history.

The JSON report records only credential-safe source metadata plus useful baseline numbers:

```json
{
  "source_id": "cnc-03-spindle",
  "source_uri": "rtsp://***:***@192.0.2.10:554/stream1",
  "elapsed_seconds": 60.02,
  "frames_read": 887,
  "capture_fps": 15.0,
  "measured_fps": 14.8,
  "observed_read_fps": 14.78
}
```

The values above are only an example shape, not measured performance from the CNC installation.

### Field test sequence

For the first real run:

1. Validate while the machine is idle for 60 seconds.
2. Validate during one complete machining cycle.
3. Briefly interrupt the camera/network path and confirm the reconnect behavior.
4. Compare reported FPS, measured FPS and observed read FPS.
5. Check the saved frame for the intended spindle/tool ROI.
6. Watch for vibration-induced view drift, glare, coolant obscuration and cable movement.
7. Repeat with a lower-bandwidth stream if the target multi-camera PC cannot sustain the primary stream.

Keep all generated reports and snapshots under `data/`; that directory is ignored by Git so production imagery and machine details are not published accidentally.

## Basic usage

```python
import os

from factorylens.sources import RTSPSource

source = RTSPSource(
    os.environ["FACTORYLENS_RTSP_URL"],
    source_id="cnc-03-spindle",
)

with source:
    for packet in source.frames(max_frames=100):
        frame = packet.frame
        print(packet.timestamp, packet.capture_fps, packet.measured_fps)
```

`FramePacket.source_uri` is credential-redacted before it can be used as metadata or logging context.

## Reconnect behavior

A transient failed frame read triggers a reconnect attempt. The default behavior is conservative:

- reconnect delay: 1 second;
- reconnect attempts: 3;
- after reconnect, one fresh frame read is attempted;
- if the stream remains unavailable, `ConnectionError` is raised.

Higher-level services should decide whether to restart the source, alert an operator, or mark the camera offline.

## Stream selection

For cameras exposing multiple RTSP streams:

- use the higher-quality stream when visual detail is required and bandwidth/CPU allow it;
- use a lower-bandwidth stream for baseline connectivity tests or CPU-constrained multi-camera deployments;
- benchmark the actual camera and network rather than assuming nominal FPS.

FactoryLens exposes both reported capture FPS and measured processing FPS so callers can observe the difference.

## Scope boundary

The RTSP adapter does **not** perform:

- three-finger gesture recognition;
- object/tool detection;
- voice capture;
- machine-cycle inference;
- video evidence recording.

Those are separate adapters/services. Keeping this boundary small makes the camera source easier to test and replace.

## Industrial deployment notes

A successful software connection is only half of a reliable camera installation. The physical mounting should also be checked for:

- rigid bracket construction and vibration resistance;
- a stable view of the intended ROI;
- clearance from spindle, tool changer, workpiece, fixture, and coolant lines;
- protection from chips, coolant and oil without blocking the lens or microphone;
- strain relief and safe cable routing;
- lighting and reflection changes across actual machining cycles.

FactoryLens is an observation system, not a safety controller. Camera status or computer-vision output must never replace certified machine guarding, interlocks, emergency stops or safety PLC logic.
