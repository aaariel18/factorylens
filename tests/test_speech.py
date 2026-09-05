from __future__ import annotations

import pytest

from factorylens.events import EventType
from factorylens.speech import JobContextNormalizer, Transcript


def test_normalizes_canonical_material_and_indonesian_process() -> None:
    result = JobContextNormalizer().normalize("Bahan S45C. Proses penghalusan.")

    assert result.ready is True
    assert result.material == "S45C"
    assert result.process == "finishing"
    assert result.material_match is not None
    assert result.process_match is not None
    assert result.process_match.alias == "penghalusan"


def test_normalizes_spoken_letter_variant_for_s45c() -> None:
    result = JobContextNormalizer().normalize(
        "bahan es empat lima ce proses penghalusan"
    )

    assert result.ready is True
    assert result.material == "S45C"
    assert result.process == "finishing"


def test_normalizes_sus304_and_drilling() -> None:
    result = JobContextNormalizer().normalize(
        "material sus tiga nol empat process drilling"
    )

    assert result.ready is True
    assert result.material == "SUS304"
    assert result.process == "drilling"


def test_ambiguous_material_requires_review_and_cannot_emit_context_event() -> None:
    result = JobContextNormalizer().normalize(
        "bahan S45C atau SUS304 proses finishing"
    )

    assert result.ready is False
    assert result.material is None
    assert "material_ambiguous" in result.issues
    with pytest.raises(ValueError, match="not ready"):
        result.to_event("cnc-03")


def test_missing_process_requires_review() -> None:
    result = JobContextNormalizer().normalize("bahan S45C")

    assert result.ready is False
    assert result.material == "S45C"
    assert result.process is None
    assert "process_missing" in result.issues


def test_low_transcript_confidence_is_not_silently_accepted() -> None:
    result = JobContextNormalizer(min_transcript_confidence=0.55).normalize(
        Transcript(
            text="bahan S45C proses penghalusan",
            language="id",
            confidence=0.31,
        )
    )

    assert result.ready is False
    assert result.material == "S45C"
    assert result.process == "finishing"
    assert "transcript_low_confidence" in result.issues


def test_ready_context_emits_job_context_event() -> None:
    result = JobContextNormalizer().normalize(
        Transcript(
            text="bahan S45C proses penghalusan",
            language="id",
            confidence=0.91,
        )
    )

    event = result.to_event("cnc-03")

    assert event.event_type is EventType.JOB_CONTEXT_SET
    assert event.job == {"material": "S45C", "process": "finishing"}
    assert event.data["transcript_confidence"] == 0.91
