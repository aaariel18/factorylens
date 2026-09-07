from datetime import UTC, datetime
from pathlib import Path

from factorylens.prelaunch import build_prelaunch_demo, run_prelaunch_demo


def test_prelaunch_demo_is_explicitly_simulated() -> None:
    steps = build_prelaunch_demo(started_at=datetime(2026, 9, 7, tzinfo=UTC))

    assert steps[0].label == "SIMULATION"
    assert "simulated" in steps[0].detail.lower()
    assert steps[-1].at_seconds == 45
    assert any(step.label == "MACHINE START" for step in steps)
    assert any(step.label == "JOB BUNDLE" for step in steps)


def test_prelaunch_demo_writes_timeline_and_manifest(tmp_path: Path) -> None:
    result = run_prelaunch_demo(output_dir=tmp_path, duration_seconds=1.0, realtime=False)

    assert result.timeline_path.exists()
    assert result.manifest_path.exists()
    manifest = result.manifest_path.read_text(encoding="utf-8")
    assert '"simulation": true' in manifest
    assert '"field_validated": false' in manifest
    assert '"material": "S45C"' in manifest
    assert '"process": "finishing"' in manifest
