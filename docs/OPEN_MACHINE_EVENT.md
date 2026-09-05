# Draft: Open Machine Event 0.1

Open Machine Event (OME) is a small experimental event envelope used by FactoryLens. It is not a formal industry standard.

The goal is to let camera adapters, PLC readers, detectors, recorders, dashboards, and external integrations exchange machine observations without inventing a new payload for every connector.

## Example

```json
{
  "schema_version": "0.1",
  "machine": {
    "id": "cnc-03",
    "type": "cnc_milling"
  },
  "event": {
    "type": "machine_cycle_started",
    "timestamp": "2026-09-05T02:14:22+00:00"
  },
  "job": {
    "material": "S45C",
    "process": "finishing"
  },
  "data": {
    "trigger_source": "modbus"
  },
  "evidence": [
    {
      "kind": "snapshot",
      "uri": "file:///data/jobs/job-001/start.jpg",
      "media_type": "image/jpeg",
      "sha256": null
    }
  ]
}
```

## Required fields

- `schema_version`
- `machine.id`
- `machine.type`
- `event.type`
- `event.timestamp`

## Optional fields

### `job`
Human or production context such as material, operation, work order, or batch. Deployments should avoid putting unnecessary personal data here.

### `data`
Event-specific structured metadata. Examples: detector confidence, trigger source, PLC register state, or gesture label.

### `evidence`
References to files or objects associated with the event.

## Event naming

Use lowercase `snake_case`, past-tense facts where practical:

- `gesture_triggered`
- `job_context_set`
- `machine_cycle_started`
- `machine_cycle_finished`
- `snapshot_captured`
- `anomaly_detected`

## Timestamps

Use ISO 8601 timestamps with timezone information. UTC is recommended for storage.

## Stability

Version `0.x` is experimental. Fields may change as real machine integrations expose better requirements.
