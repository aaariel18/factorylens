# FactoryLens Roadmap

The roadmap favors a small, composable core over a giant first release.

## v0.1 — Event core and one CNC story

- [x] machine-event data model
- [x] operator-context / machine-cycle state machine
- [x] CLI demo
- [x] draft Open Machine Event format
- [ ] RTSP camera adapter
- [ ] three-finger gesture trigger
- [ ] audio capture with a 120-second maximum and silence stop
- [ ] speech-to-text adapter
- [ ] material/process normalizer
- [ ] machine-start trigger interface
- [ ] snapshots at cycle start
- [ ] event video recorder with pre-roll

## v0.2 — Reliable edge recording

- [ ] RTSP reconnect strategy
- [ ] audio/video synchronization
- [ ] configurable evidence retention
- [ ] multi-camera source registry
- [ ] H.264/MP4 recording path
- [ ] checksums and event evidence manifest
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
