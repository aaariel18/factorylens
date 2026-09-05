import pytest

from factorylens.session import MachineSession, SessionState


def test_happy_path_cycle() -> None:
    session = MachineSession("cnc-01", "cnc_milling")

    session.trigger_operator_note()
    assert session.state == SessionState.LISTENING

    context_event = session.set_job_context(material="S45C", process="finishing")
    assert context_event.job == {"material": "S45C", "process": "finishing"}
    assert session.state == SessionState.ARMED

    session.machine_started()
    assert session.state == SessionState.RECORDING

    session.machine_finished()
    assert session.state == SessionState.COMPLETE


def test_cycle_cannot_start_without_context() -> None:
    session = MachineSession("cnc-01")
    with pytest.raises(RuntimeError):
        session.machine_started()
