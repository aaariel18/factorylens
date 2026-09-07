from datetime import UTC, datetime, timedelta

import factorylens.cycle
import factorylens.events
import factorylens.simulation

BASE = datetime(2026, 9, 7, 1, 0, tzinfo=UTC)


def observation(
    seconds: float,
    *,
    running: bool,
    kind: factorylens.cycle.MachineSignalKind = factorylens.cycle.MachineSignalKind.CONTROLLER,
    confidence: float = 1.0,
) -> factorylens.cycle.MachineStateObservation:
    return factorylens.cycle.MachineStateObservation(
        running=running,
        timestamp=BASE + timedelta(seconds=seconds),
        source_id="cnc-03-run",
        kind=kind,
        confidence=confidence,
    )


def test_cycle_start_and_finish_are_debounced() -> None:
    trigger = factorylens.cycle.DebouncedCycleTrigger(
        "cnc-03",
        machine_type="cnc_milling",
        config=factorylens.cycle.CycleTriggerConfig(
            start_stability_seconds=0.5,
            stop_stability_seconds=0.5,
        ),
    )

    first = trigger.process(observation(0.0, running=True))
    started = trigger.process(observation(0.6, running=True))
    stopping = trigger.process(observation(3.0, running=False))
    finished = trigger.process(observation(3.6, running=False))

    assert first.reason == "debouncing"
    assert started.event is not None
    assert started.event.event_type is factorylens.events.EventType.MACHINE_CYCLE_STARTED
    assert started.event.data["signal_class"] == "measured"
    assert started.event.data["trigger_source"] == "cnc-03-run"
    assert stopping.reason == "debouncing"
    assert finished.event is not None
    assert finished.event.event_type is factorylens.events.EventType.MACHINE_CYCLE_FINISHED


def test_visual_machine_state_is_explicitly_inferred() -> None:
    trigger = factorylens.cycle.DebouncedCycleTrigger(
        "cnc-03",
        config=factorylens.cycle.CycleTriggerConfig(start_stability_seconds=0.0),
    )
    result = trigger.process(
        observation(
            0.0,
            running=True,
            kind=factorylens.cycle.MachineSignalKind.VISUAL,
        ),
    )

    assert result.event is not None
    assert result.event.data["signal_kind"] == "visual"
    assert result.event.data["signal_class"] == "inferred"


def test_low_confidence_observation_does_not_advance_state() -> None:
    trigger = factorylens.cycle.DebouncedCycleTrigger(
        "cnc-03",
        config=factorylens.cycle.CycleTriggerConfig(
            start_stability_seconds=0.0,
            min_confidence=0.8,
        ),
    )
    result = trigger.process(observation(0.0, running=True, confidence=0.5))

    assert result.event is None
    assert result.reason == "low_confidence"
    assert trigger.stable_running is False


def test_simulated_signal_is_a_safe_development_double() -> None:
    signal = factorylens.simulation.SimulatedMachineSignal("dev-cnc")
    result = signal.observe(True, timestamp=BASE)

    assert result.running is True
    assert result.kind is factorylens.cycle.MachineSignalKind.SIMULATED
    assert result.kind.signal_class == "simulated"
