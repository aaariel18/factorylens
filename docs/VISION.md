# Vision: the Legacy Machine Visibility Problem

Industrial machines can remain mechanically useful long after their software interfaces become outdated.

A machine may cut metal precisely for twenty years while still being unable to tell modern software:

- what job is running;
- what material the operator installed;
- when a cycle started;
- what happened immediately before a tool problem;
- which camera evidence belongs to which production cycle.

This is the **Legacy Machine Visibility Problem**.

FactoryLens explores a vendor-neutral layer between raw machine signals and higher-level manufacturing software. It should be possible to attach useful observability without replacing the machine controller.

> Bring modern observability to machines that were never designed to be observable.

## Human-to-machine metadata

Not all production context exists in a PLC register. Operators often know the missing information.

A gesture plus a short voice note can become structured context:

```text
3-finger gesture
      ↓
"Material S45C, process finishing"
      ↓
{ material: "S45C", process: "finishing" }
      ↓
next machine cycle
```

That context can then travel with snapshots, recordings, detections, and machine-state events.

## What FactoryLens is not

FactoryLens is not an MES replacement, a certified safety system, or a promise that computer vision can infer every machine condition. It should integrate with reliable machine signals when they exist and clearly label inferred states when they do not.
