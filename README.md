# FactoryLens

<p align="center">
  <img src="docs/assets/social-preview.svg" alt="FactoryLens social preview" width="100%" />
</p>

**Open-source observability and black-box recording for machines that don't have APIs.**

FactoryLens is an early-stage open-source project for bringing modern observability to legacy industrial machines using cameras, audio, machine signals, and event-driven evidence capture.

> Turn a machine that can only *run* into a machine that can also *explain what happened*.

## Why FactoryLens?

Many CNC machines, mills, lathes, injection molding machines, laser cutters, and workshop machines can operate reliably for decades but expose little or no modern telemetry. Production context is often scattered across CCTV, PLC signals, spreadsheets, operator notes, and memory.

FactoryLens aims to unify those signals into one machine timeline:

```text
Camera / RTSP ───────┐
Microphone ──────────┤
Gesture ─────────────┤
PLC / Modbus / GPIO ─┼──> FactoryLens ──> Machine Event Timeline
Sensors ─────────────┘                    ├─ snapshots
                                          ├─ video
                                          ├─ audio
                                          └─ structured metadata
```

## Flagship CNC workflow

```text
Operator shows 3 fingers
        ↓
Capture an operator voice note
        ↓
"Bahan S45C, proses penghalusan"
        ↓
Speech-to-text + controlled normalization
        ↓
JOB_CONTEXT_SET
        ↓
Wait for a stable machine-running signal
        ↓
MACHINE_CYCLE_STARTED
        ↓
Flush video pre-roll + capture 0s / +2s / +10s snapshots
        ↓
Record the machining cycle
        ↓
MACHINE_CYCLE_FINISHED
        ↓
Write one evidence manifest for the job
```

The long-term idea is **human-to-machine metadata**: let operators attach production context to a machine without stopping to use a keyboard.

## Try it without a camera or CNC

The pre-launch demo is deliberately hardware-free and marks its machine signal as **simulated**.

```bash
python -m pip install -e ".[dev]"
python examples/prelaunch_demo.py --realtime --duration 45
```

For an instant preview without waiting 45 seconds:

```bash
python examples/prelaunch_demo.py
```

It writes a simulated `timeline.jsonl` and `manifest.json` under `data/prelaunch-demo/`. The demo exists to explain the architecture while the real CNC field-validation gates are still open. The first physical camera installation is now complete, but the simulated demo is **not** presented as real machining evidence.

See [docs/PRELAUNCH.md](docs/PRELAUNCH.md) for the public demo and launch playbook.

## Current status

FactoryLens is **pre-alpha**. The v0.1 software path now includes:

- machine-event and session state models;
- reconnect-capable RTSP frame capture with credential-safe metadata;
- RTSP field-validation CLI;
- three-finger gesture trigger with ROI, hold time, confidence, cooldown, and frame sampling;
- optional MediaPipe hand-landmark adapter;
- FFmpeg RTSP operator voice-note capture with a 120-second ceiling and silence stop;
- offline-first speech-to-text interface with an optional faster-whisper adapter;
- deterministic material/process normalization with Indonesian spoken aliases and ambiguity gates;
- PLC-first, vendor-neutral machine-cycle triggering with measured/inferred signal provenance and debounce;
- a simulated machine-state source for development without a physical CNC;
- cycle evidence recording with decoded-frame pre-roll, MP4 output, and default snapshots at 0s / +2s / +10s;
- one JSON job manifest that groups machine/job context and evidence events;
- `CNCWorkflow`, which connects armed job context, machine-cycle events, and evidence capture;
- a 45-second pre-launch simulation for public demos without hardware;
- **first physical camera installation on the CNC completed for field testing**;
- automated tests and CI across Python 3.11 and 3.12.

The software path and first camera installation are complete, but **real CNC field validation is still required** for RTSP stability, gesture accuracy, microphone quality, speech normalization, machine-run signal mapping, and a complete machining-cycle evidence bundle. FactoryLens is not a safety system or the sole source of machine-state truth.

## CNC field prototype

![FactoryLens CNC field prototype](docs/assets/factorylens-field-prototype.jpg)

The first physical camera has now been installed on the CNC prototype bracket. The installation provides a close observation angle toward the spindle/work area and moves the project from camera-placement experiments into real field-validation work. Mounting, collision/vibration, ROI, cable-routing, stream stability, and audio still require validation under actual machine operation.

See [docs/FIELD_PROTOTYPE.md](docs/FIELD_PROTOTYPE.md).

## Quick start

Requires Python 3.11+.

```bash
git clone https://github.com/aaariel18/factorylens.git
cd factorylens
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
python -m pip install -e ".[dev]"
factorylens demo-event --output demo-event.jsonl
pytest
```

### Validate a real RTSP camera

```bash
python -m pip install -e ".[camera]"
export FACTORYLENS_RTSP_URL='rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1'

factorylens validate-rtsp \
  --source-id cnc-03-spindle \
  --duration 60 \
  --snapshot data/validation/cnc-03-first-frame.jpg \
  --report data/validation/cnc-03-rtsp-report.json
```

The `data/` directory is Git-ignored. Validation reports store RTSP URIs with credentials redacted.

### Test the three-finger trigger

```bash
python -m pip install -e ".[camera,gesture]"
python examples/cnc/gesture_trigger_demo.py
```

### Capture an operator voice note

Install FFmpeg, then run:

```bash
factorylens capture-operator-note \
  --machine-id cnc-03 \
  --source-id cnc-03-spindle \
  --max-seconds 120 \
  --silence-seconds 3
```

### Test job-context normalization

```bash
factorylens normalize-job-text \
  "bahan es empat lima ce proses penghalusan" \
  --confidence 0.91 \
  --machine-id cnc-03
```

For local speech-to-text, pre-stage a faster-whisper model:

```bash
python -m pip install -e ".[speech]"
factorylens transcribe-operator-note \
  data/operator-notes/cnc-03_YYYYMMDD_HHMMSS.wav \
  --model /path/to/local-whisper-model \
  --language id \
  --machine-id cnc-03
```

## Machine-cycle and evidence APIs

FactoryLens intentionally keeps the machine-state adapter independent from the CNC vendor. Convert controller/PLC/Modbus/OPC UA/GPIO/visual state into a `MachineStateObservation`, then let `DebouncedCycleTrigger` emit stable cycle events.

`JobEvidenceRecorder` continuously buffers recent camera frames. On cycle start it flushes pre-roll into the video, captures scheduled snapshots, and on cycle finish writes a job manifest.

See:

- [docs/MACHINE_CYCLE.md](docs/MACHINE_CYCLE.md)
- [docs/EVIDENCE_RECORDING.md](docs/EVIDENCE_RECORDING.md)
- [docs/RTSP_CAMERA.md](docs/RTSP_CAMERA.md)
- [docs/GESTURE_TRIGGER.md](docs/GESTURE_TRIGGER.md)
- [docs/AUDIO_CAPTURE.md](docs/AUDIO_CAPTURE.md)
- [docs/SPEECH_JOB_CONTEXT.md](docs/SPEECH_JOB_CONTEXT.md)

## Design principles

1. **Legacy-first** — useful even when a machine has no cloud API.
2. **Event-first** — every important observation becomes a timestamped event.
3. **Evidence-first** — events can point to video, audio, snapshots, and metadata.
4. **Edge-friendly** — local processing should be the default path.
5. **Vendor-neutral** — RTSP, ONVIF, Modbus, OPC UA, MQTT, GPIO, and custom adapters.
6. **Human-friendly** — operators should not need a developer console to add context.
7. **Safe by default** — FactoryLens observes and records; machine control must remain explicit and isolated.

## Integration status

- [x] RTSP frame source with reconnect and frame metadata
- [x] RTSP field-validation CLI harness
- [x] three-finger gesture trigger core + optional hand-landmark adapter
- [x] bounded RTSP operator audio capture through FFmpeg
- [x] pluggable offline speech-to-text interface + optional faster-whisper adapter
- [x] controlled material/process normalizer with ambiguity/confidence gating
- [x] vendor-neutral debounced machine-cycle trigger interface
- [x] explicit measured/inferred/simulated signal provenance
- [x] decoded-frame video pre-roll + start snapshots + job evidence manifest
- [x] end-to-end CNC workflow orchestration test
- [x] hardware-free pre-launch simulation
- [x] first physical CNC camera installation completed
- [ ] RTSP stability validated through a complete real machining cycle
- [ ] field-calibrated gesture accuracy on the real CNC installation
- [ ] field-validated microphone quality and silence settings
- [ ] field-validated speech vocabulary and transcription accuracy
- [ ] first real CNC run-signal adapter/configuration
- [ ] complete real machining-cycle evidence validation
- [ ] Modbus / OPC UA / GPIO concrete adapters
- [ ] detector plugin API and OpenVINO industrial-vision reference adapter
- [ ] compressed/encoded pre-roll suitable for multi-camera production
- [ ] dashboard and searchable machine timeline

See [ROADMAP.md](ROADMAP.md) for the staged plan.

## Help shape the project

You do **not** need access to a CNC to contribute. Good first contributions include small adapters, docs, test fixtures, CLI improvements, event-schema feedback, and deployment examples.

See the open issues, especially those marked `good first issue`, and read [CONTRIBUTING.md](CONTRIBUTING.md).

For maintainers preparing public posts, the copy-ready launch kit is in [docs/LAUNCH_POSTS.md](docs/LAUNCH_POSTS.md).

## Security

Never commit RTSP usernames/passwords, camera accounts, PLC credentials, internal IP inventories, production video, operator audio, transcripts, or `.env` files. Use `.env.example` only as a template.

See [SECURITY.md](SECURITY.md).

## License

MIT. See [LICENSE](LICENSE).

---

**FactoryLens is not a machine safety controller.** It must not replace certified interlocks, emergency stops, guarding, PLC safety logic, or other required industrial safety systems.
