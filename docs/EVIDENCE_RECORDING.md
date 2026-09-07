# Cycle evidence recording

`JobEvidenceRecorder` turns a machine cycle into one auditable job bundle.

## Default capture policy

- keep a 5-second decoded-frame pre-roll buffer;
- start MP4 recording when a stable cycle-start event arrives;
- flush the pre-roll into the beginning of the video;
- capture snapshots at 0, +2, and +10 seconds;
- stop video when the stable cycle-finished event arrives;
- write `manifest.json` containing machine/job metadata and the event timeline.

A typical directory is:

```text
data/jobs/cnc-03_20260907T020000Z/
├── manifest.json
├── cycle.mp4
├── start_000s.jpg
├── start_002s.jpg
└── start_010s.jpg
```

Operator audio and transcript/job-context events can be attached before cycle start so they appear in the same manifest.

## Integration

```python
from factorylens.evidence import EvidenceRecorderConfig, JobEvidenceRecorder

recorder = JobEvidenceRecorder(
    "cnc-03",
    machine_type="cnc_milling",
    config=EvidenceRecorderConfig(
        pre_roll_seconds=5.0,
        snapshot_offsets_seconds=(0.0, 2.0, 10.0),
    ),
)

# Keep feeding camera frames even while idle so pre-roll is available.
recorder.ingest(frame_packet)

# On stable machine-cycle start:
recorder.start_cycle(machine_cycle_started_event)

# Continue feeding frames during the cycle.
recorder.ingest(frame_packet)

# On stable machine-cycle finish:
result = recorder.finish_cycle(machine_cycle_finished_event)
print(result.manifest_path)
```

`CNCWorkflow` connects `MachineSession`, `DebouncedCycleTrigger`, and `JobEvidenceRecorder` so the v0.1 path can be exercised as one flow.

## Codec note

The default OpenCV backend writes an MP4 container using `mp4v` because it is broadly available in OpenCV builds. H.264 availability depends on the local OpenCV/FFmpeg build. A future encoded-packet/FFmpeg recorder can avoid decoding/re-encoding and reduce memory/CPU pressure for multi-camera deployments.

## Memory note

The current pre-roll buffer stores decoded frames. This is intentionally simple for v0.1 but can consume significant RAM at high resolution or across many cameras. For six-camera production deployment, benchmark memory and CPU usage and prefer a compressed ring buffer before treating the recorder as production-ready.

## Storage and privacy

The default `data/` path is Git-ignored. Do not commit production video, operator audio, transcripts, internal machine identifiers, or credentials to the public repository unless those artifacts are explicitly cleared for publication.

Storage failures are raised to the caller. The orchestration layer should report them as an evidence failure without using FactoryLens as a machine-control dependency.
