# FactoryLens Roadmap

The roadmap favors a small, composable core over a giant first release.

## v0.1 — Event core and one CNC story

- [x] machine-event data model
- [x] operator-context / machine-cycle state machine
- [x] CLI demo
- [x] draft Open Machine Event format
- [x] RTSP camera adapter
- [x] three-finger gesture trigger
- [x] audio capture with a 120-second maximum and silence stop
- [x] speech-to-text adapter
- [x] material/process normalizer
- [x] machine-start/finish trigger interface with measured/inferred provenance
- [x] snapshots at cycle start (default 0s / +2s / +10s)
- [x] MP4 event video recorder with decoded-frame pre-roll
- [x] one job evidence manifest that can include context, audio, snapshots and video events
- [x] end-to-end orchestration test for armed job -> cycle start -> evidence -> cycle finish

### v0.1 field-validation gates

The software path is implemented, but an alpha release is not considered field-validated until the physical CNC tests are completed:

- [ ] real RTSP stability and reconnect baseline (#10)
- [ ] three-finger gesture calibration and false-positive test (#13)
- [ ] real camera microphone / CNC noise validation (#15)
- [ ] real operator speech-to-job-context benchmark (#17)
- [ ] real machine-run signal mapping for the first CNC installation (#20)
- [ ] one complete real machining cycle producing a reviewable job evidence bundle (#21)

When all six gates are complete, review benchmark results, known limitations, and privacy/safety documentation before tagging `v0.1.0-alpha`.

## v0.2 — Reliable edge recording

- [x] RTSP reconnect strategy
- [ ] audio/video synchronization
- [ ] configurable evidence retention
- [ ] multi-camera source registry
- [ ] encoded H.264/MP4 recording path without decoded-frame pre-roll pressure
- [ ] checksums for evidence artifacts
- [x] JSON event evidence manifest
- [ ] local SQLite event store

## v0.3 — Machine signals

- [ ] Modbus TCP adapter
- [ ] OPC UA adapter
- [ ] GPIO/dry-contact adapter
- [ ] stack-light visual adapter
- [ ] MQTT event output
- [ ] webhooks

## v0.4 — Industrial computer vision toolkit

- [ ] ROI manager
- [ ] detector plugin API
- [ ] tool-presence example
- [ ] operator-hand / foreign-object example
- [ ] frame sampling and CPU-friendly inference
- [ ] OpenVINO reference adapter

## v0.5 — Dashboard

- [ ] machine list and state
- [ ] event timeline
- [ ] evidence viewer
- [ ] job search by material/process
- [ ] anomaly review workflow

## v1.0 — Stable integration platform

- stable event schema
- documented plugin contracts
- migration policy
- example deployments on multiple machine families
- production hardening and benchmark documentation

## Parallel community tracks

### OpenFactory Dataset

A future public, rights-cleared dataset for industrial vision tasks such as tool presence, machine state, door state, coolant state, and other observable conditions.

### Integrations

Potential adapters include Fanuc, Siemens, Mitsubishi, Omron, Keyence, Haas, Arduino, ESP32, Node-RED, Grafana, and Home Assistant. Brand names describe potential interoperability targets, not endorsements.
