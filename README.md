# FactoryLens

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

## Flagship workflow

The first CNC workflow is intentionally simple and human-friendly:

```text
Operator shows 3 fingers
        ↓
Capture an operator voice note
        ↓
"Material S45C, process finishing"
        ↓
Normalize material + process metadata
        ↓
Wait for CNC cycle start
        ↓
Capture start snapshots + video
        ↓
Record anomaly/event evidence
        ↓
Close the cycle and save one job record
```

The long-term idea is **human-to-machine metadata**: let operators attach production context to a machine without stopping to use a keyboard.

## Example machine timeline

```text
09:13:02  GESTURE_3_FINGERS
09:13:04  OPERATOR_NOTE_STARTED
09:13:11  JOB_CONTEXT_SET        material=S45C process=finishing
09:14:22  MACHINE_CYCLE_STARTED
09:14:22  SNAPSHOT_CAPTURED
09:14:22  VIDEO_RECORDING_STARTED
09:18:41  TOOL_ANOMALY
09:18:41  EVIDENCE_CAPTURED
09:23:17  MACHINE_CYCLE_FINISHED
```

## Current status

FactoryLens is **pre-alpha**. The repository currently provides:

- a small, dependency-light machine-event core;
- a session state machine for operator context and machine cycles;
- a reconnect-capable RTSP frame source with credential-safe metadata;
- a one-command RTSP field-validation harness with JSON metrics and optional snapshot;
- a detector-independent three-finger gesture state machine with ROI, hold, cooldown and frame sampling;
- an optional MediaPipe hand-landmark adapter and CNC RTSP gesture demo;
- FFmpeg-based RTSP operator voice-note capture with a 120-second ceiling and optional silence stop;
- an offline-first pluggable speech-to-text interface with an optional faster-whisper adapter;
- a deterministic material/process normalizer with Indonesian spoken aliases and ambiguity gates;
- `job_context_set` emission only when required fields are unambiguous and confidence passes review gates;
- a CLI demo that emits an Open Machine Event JSON document;
- a draft Open Machine Event format;
- architecture, RTSP, gesture, audio, speech and CNC integration documentation;
- CI and contribution scaffolding.

PLC/Modbus and production recording adapters are planned work. The RTSP, gesture, audio and speech paths still require field validation on the real CNC installation. Do not deploy this repository as a safety system or as the sole source of machine-state truth.

## CNC field prototype

![FactoryLens CNC field prototype](docs/assets/factorylens-field-prototype.jpg)

The first physical camera-placement experiment is now documented, including mounting observations, collision/vibration concerns, ROI considerations, cable routing and the next field-validation checklist.

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

For a real RTSP camera source:

```bash
python -m pip install -e ".[camera]"
export FACTORYLENS_RTSP_URL='rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1'

factorylens validate-rtsp \
  --source-id cnc-03-spindle \
  --duration 60 \
  --snapshot data/validation/cnc-03-first-frame.jpg \
  --report data/validation/cnc-03-rtsp-report.json
```

The report and snapshot remain under the Git-ignored `data/` directory. The report stores the RTSP source URI with credentials redacted.

To test the three-finger operator trigger after the RTSP baseline is stable:

```bash
python -m pip install -e ".[camera,gesture]"
python examples/cnc/gesture_trigger_demo.py
```

To capture the operator voice note from the camera's RTSP audio track, install FFmpeg and run:

```bash
factorylens capture-operator-note \
  --machine-id cnc-03 \
  --source-id cnc-03-spindle \
  --max-seconds 120 \
  --silence-seconds 3
```

Test job normalization without any speech model:

```bash
factorylens normalize-job-text \
  "bahan es empat lima ce proses penghalusan" \
  --confidence 0.91 \
  --machine-id cnc-03
```

For local speech-to-text, pre-stage a faster-whisper model and run:

```bash
python -m pip install -e ".[speech]"
factorylens transcribe-operator-note \
  data/operator-notes/cnc-03_YYYYMMDD_HHMMSS.wav \
  --model /path/to/local-whisper-model \
  --language id \
  --machine-id cnc-03
```

See [docs/RTSP_CAMERA.md](docs/RTSP_CAMERA.md), [docs/GESTURE_TRIGGER.md](docs/GESTURE_TRIGGER.md), [docs/AUDIO_CAPTURE.md](docs/AUDIO_CAPTURE.md) and [docs/SPEECH_JOB_CONTEXT.md](docs/SPEECH_JOB_CONTEXT.md).

## Design principles

1. **Legacy-first** — useful even when a machine has no cloud API.
2. **Event-first** — every important observation becomes a timestamped event.
3. **Evidence-first** — events can point to video, audio, snapshots, and metadata.
4. **Edge-friendly** — local processing should be the default path.
5. **Vendor-neutral** — RTSP, ONVIF, Modbus, OPC UA, MQTT, GPIO, and custom adapters.
6. **Human-friendly** — operators should not need a developer console to add context.
7. **Safe by default** — FactoryLens observes and records; machine control must remain explicit and isolated.

## Repository map

```text
src/factorylens/       event core, session model, validation, sources, audio, speech and vision
examples/cnc/          CNC configuration, simulation and field demos
docs/                  architecture, event format, setup guides and project vision
tests/                 unit tests
.github/workflows/     CI
```

## Integration status

- [x] RTSP frame source with reconnect and frame metadata
- [x] RTSP field-validation CLI harness
- [x] three-finger gesture trigger core + optional hand-landmark adapter
- [ ] field-calibrated gesture accuracy on the real CNC installation
- [x] bounded RTSP operator audio capture through FFmpeg
- [ ] field-validated speech quality and silence settings on the real CNC installation
- [x] pluggable offline speech-to-text interface + optional faster-whisper adapter
- [x] controlled material/process normalizer with ambiguity/confidence gating
- [ ] field-validated vocabulary and transcription accuracy on real operator audio
- [ ] ONVIF discovery/control metadata
- [ ] Modbus machine-state adapter
- [ ] OPC UA adapter
- [ ] MQTT and webhook outputs
- [ ] pre-roll video buffer
- [ ] multi-camera evidence capture
- [ ] dashboard and searchable machine timeline

See [ROADMAP.md](ROADMAP.md) for the staged plan.

## Open Machine Event

FactoryLens is also experimenting with a small vendor-neutral event envelope so machine observations can move between cameras, PLC adapters, dashboards, and analytics tools without each integration inventing a new format.

See [docs/OPEN_MACHINE_EVENT.md](docs/OPEN_MACHINE_EVENT.md).

## Security

Never commit RTSP usernames/passwords, camera accounts, PLC credentials, internal IP inventories, production video, operator audio, transcripts, or `.env` files. Use `.env.example` only as a template.

See [SECURITY.md](SECURITY.md).

## Contributing

The project is intentionally young. Architecture feedback, machine integration stories, documentation fixes, and small adapters are especially welcome.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and check the open issues.

## License

MIT. See [LICENSE](LICENSE).

---

**FactoryLens is not a machine safety controller.** It must not replace certified interlocks, emergency stops, guarding, PLC safety logic, or other required industrial safety systems.
