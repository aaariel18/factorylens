# Machine-cycle triggering

FactoryLens v0.1 separates **job context** from **machine state**. Operator speech can arm a job, but recording only starts after a stable machine-running signal is observed.

## Trust order

Prefer machine-state sources in this order when they are available:

1. controller / PLC run bit;
2. digital I/O, Modbus, OPC UA, or GPIO adapter;
3. visual inference such as stack-light or spindle-state detection.

`DebouncedCycleTrigger` records the origin in every event:

- `signal_kind`: controller, digital_io, modbus, opc_ua, gpio, visual, or simulated;
- `signal_class`: `measured`, `inferred`, or `simulated`;
- `trigger_source`: adapter/source identifier;
- `confidence`;
- `debounce_seconds`.

This prevents a camera-derived guess from looking identical to a controller signal in downstream data.

## Debounce

The trigger requires a state change to remain stable for a configurable interval before emitting `machine_cycle_started` or `machine_cycle_finished`.

```python
from factorylens.cycle import CycleTriggerConfig, DebouncedCycleTrigger

trigger = DebouncedCycleTrigger(
    "cnc-03",
    machine_type="cnc_milling",
    config=CycleTriggerConfig(
        start_stability_seconds=0.5,
        stop_stability_seconds=0.5,
    ),
)
```

Adapters should convert their native value into `MachineStateObservation` rather than coupling the FactoryLens core to one PLC vendor.

## Development without a CNC

`SimulatedMachineSignal` is a test double for demos and automated tests:

```python
from factorylens.simulation import SimulatedMachineSignal

signal = SimulatedMachineSignal("dev-run-bit")
observation = signal.observe(True)
result = trigger.process(observation)
```

## Safety boundary

FactoryLens machine-state signals are observability inputs only. They must not replace certified interlocks, emergency stops, guarding, safety PLC logic, or any other required machine-safety function. A visually inferred state is explicitly marked `inferred` and must not be represented as a controller truth signal.
