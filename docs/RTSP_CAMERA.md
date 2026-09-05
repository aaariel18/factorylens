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
