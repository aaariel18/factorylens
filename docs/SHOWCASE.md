# FactoryLens Project Showcase

**Open-source observability and black-box recording for machines that don't have APIs.**

FactoryLens is a pre-alpha open-source project for bringing modern observability to legacy industrial machines through cameras, operator context, machine signals, and event-driven evidence capture.

![FactoryLens social preview](assets/social-preview.svg)

## Current milestone

The first physical camera installation on the CNC prototype is now complete. The project is moving from software-only simulation and camera-placement work into **real CNC field validation**.

![FactoryLens CNC field prototype](assets/factorylens-field-prototype.jpg)

The installed camera provides a close view of the spindle/work area. Before the installation is treated as production-ready, FactoryLens still needs field validation for RTSP stability, vibration, ROI stability, microphone quality, speech recognition, machine RUN/STOP mapping, and one complete machining-cycle evidence bundle.

## What the software path already includes

- reconnect-capable RTSP frame capture;
- three-finger operator trigger;
- bounded operator voice-note capture;
- offline-first speech-to-text interface;
- controlled material/process normalization;
- vendor-neutral machine-cycle events with debounce and signal provenance;
- video pre-roll and cycle snapshots;
- job evidence manifests;
- a hardware-free simulated CNC workflow for development and public demonstration;
- automated tests and CI across Python 3.11 and 3.12.

## Flagship workflow

```text
3-finger gesture
      ↓
operator voice note
      ↓
"S45C, finishing"
      ↓
structured job context
      ↓
wait for machine RUN
      ↓
pre-roll + snapshots + cycle recording
      ↓
machine STOP
      ↓
job evidence bundle
```

## Why it exists

Many industrial machines can manufacture parts for years while exposing little modern telemetry. FactoryLens explores a vendor-neutral observability layer for machines where production context would otherwise be scattered across CCTV, PLC signals, operator notes, spreadsheets, and memory.

## Project links

- **Repository:** https://github.com/aaariel18/factorylens
- **Field prototype notes:** [FIELD_PROTOTYPE.md](FIELD_PROTOTYPE.md)
- **Architecture:** [ARCHITECTURE.md](ARCHITECTURE.md)
- **Roadmap:** [../ROADMAP.md](../ROADMAP.md)
- **Contributing:** [../CONTRIBUTING.md](../CONTRIBUTING.md)

## Status boundary

FactoryLens is **pre-alpha** and is not a machine safety controller. The first camera is physically mounted, but real machining-cycle validation is still in progress. Simulated events are explicitly marked as simulated and must not be presented as production evidence.
