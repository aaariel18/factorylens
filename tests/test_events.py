from factorylens.events import EventType, MachineEvent


def test_machine_event_shape() -> None:
    event = MachineEvent(
        event_type=EventType.MACHINE_CYCLE_STARTED,
        machine_id="cnc-03",
        machine_type="cnc_milling",
        job={"material": "S45C", "process": "finishing"},
    )

    payload = event.to_dict()

    assert payload["schema_version"] == "0.1"
    assert payload["machine"] == {"id": "cnc-03", "type": "cnc_milling"}
    assert payload["event"]["type"] == "machine_cycle_started"
    assert payload["job"]["material"] == "S45C"
