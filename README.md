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
- a CLI demo that emits an Open Machine Event JSON document;
- a draft Open Machine Event format;
- architecture, RTSP and CNC integration documentation;
- CI and contribution scaffolding.

The hand-gesture, RTSP-audio, speech-to-text, PLC/Modbus, and production recording adapters are planned work. Do not deploy this repository as a safety system or as the sole source of machine-state truth.

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

See [docs/RTSP_CAMERA.md](docs/RTSP_CAMERA.md).

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
src/factorylens/       event core, session model, validation and source adapters
examples/cnc/          CNC example configuration and simulation
docs/                  architecture, event format, camera setup and project vision
tests/                 unit tests
.github/workflows/     CI
```

## Integration status

- [x] RTSP frame source with reconnect and frame metadata
- [x] RTSP field-validation CLI harness
- [ ] ONVIF discovery/control metadata
- [ ] hand gesture trigger
- [ ] microphone / RTSP audio capture
- [ ] offline speech-to-text
- [ ] material and process normalizer
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

Never commit RTSP usernames/passwords, camera accounts, PLC credentials, internal IP inventories, production video, or `.env` files. Use `.env.example` only as a template.

See [SECURITY.md](SECURITY.md).

## Contributing

The project is intentionally young. Architecture feedback, machine integration stories, documentation fixes, and small adapters are especially welcome.

Read [CONTRIBUTING.md](CONTRIBUTING.md) and check the open issues.

## License

MIT. See [LICENSE](LICENSE).

---

**FactoryLens is not a machine safety controller.** It must not replace certified interlocks, emergency stops, guarding, PLC safety logic, or other required industrial safety systems.
