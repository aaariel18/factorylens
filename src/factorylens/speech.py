from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from .events import EventType, MachineEvent


@dataclass(frozen=True, slots=True)
class Transcript:
    text: str
    language: str | None = None
    confidence: float | None = None

    def __post_init__(self) -> None:
        if self.confidence is not None and not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1 or None")


class SpeechToText(Protocol):
    def transcribe(self, audio_path: str | Path, *, language: str | None = "id") -> Transcript: ...


@dataclass(frozen=True, slots=True)
class VocabularyMatch:
    canonical: str
    alias: str
    confidence: float
    scope: str


@dataclass(frozen=True, slots=True)
class JobVocabulary:
    materials: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    processes: Mapping[str, tuple[str, ...]] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class JobContextResult:
    transcript: str
    material: str | None
    process: str | None
    transcript_confidence: float | None
    material_match: VocabularyMatch | None
    process_match: VocabularyMatch | None
    issues: tuple[str, ...]
    ready: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "transcript": self.transcript,
            "transcript_confidence": self.transcript_confidence,
            "material": self.material,
            "process": self.process,
            "material_match": _match_to_dict(self.material_match),
            "process_match": _match_to_dict(self.process_match),
            "issues": list(self.issues),
            "ready": self.ready,
        }

    def to_json(self, *, indent: int | None = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_event(self, machine_id: str, machine_type: str = "cnc_milling") -> MachineEvent:
        if not self.ready or self.material is None or self.process is None:
            raise ValueError("job context is not ready; review missing or ambiguous fields first")
        return MachineEvent(
            event_type=EventType.JOB_CONTEXT_SET,
            machine_id=machine_id,
            machine_type=machine_type,
            job={"material": self.material, "process": self.process},
            data={
                "transcript": self.transcript,
                "transcript_confidence": self.transcript_confidence,
                "material_alias": self.material_match.alias if self.material_match else None,
                "process_alias": self.process_match.alias if self.process_match else None,
            },
        )


def _match_to_dict(match: VocabularyMatch | None) -> dict[str, object] | None:
    if match is None:
        return None
    return {
        "canonical": match.canonical,
        "alias": match.alias,
        "confidence": match.confidence,
        "scope": match.scope,
    }


def default_job_vocabulary() -> JobVocabulary:
    """Small starter vocabulary intended to be replaced/extended by each factory."""

    return JobVocabulary(
        materials={
            "S45C": (
                "s45c",
                "s 45 c",
                "s empat lima c",
                "es empat lima ce",
                "es empat lima c",
                "s empat lima ce",
            ),
            "S50C": (
                "s50c",
                "s 50 c",
                "s lima nol c",
                "es lima nol ce",
                "es lima puluh ce",
            ),
            "SUS304": (
                "sus304",
                "sus 304",
                "sus tiga nol empat",
                "es yu es tiga nol empat",
            ),
            "A6061": (
                "a6061",
                "a 6061",
                "a enam nol enam satu",
                "aluminium 6061",
                "aluminum 6061",
            ),
            "SKD11": (
                "skd11",
                "skd 11",
                "es ka de sebelas",
                "skd sebelas",
            ),
        },
        processes={
            "finishing": (
                "finishing",
                "finish",
                "penghalusan",
                "proses penghalusan",
            ),
            "roughing": (
                "roughing",
                "rough",
                "pengasaran",
                "proses pengasaran",
            ),
            "drilling": (
                "drilling",
                "drill",
                "pengeboran",
                "bor",
            ),
            "facing": (
                "facing",
                "face milling",
                "perataan muka",
            ),
            "milling": (
                "milling",
                "mill",
                "frais",
            ),
        },
    )


_NON_WORD = re.compile(r"[^0-9a-zA-Z]+")
_SPACE = re.compile(r"\s+")
_MATERIAL_SCOPE = re.compile(
    r"\b(?:bahan|material)\b\s*(?P<value>.*?)(?=\b(?:proses|process)\b|$)",
    re.IGNORECASE,
)
_PROCESS_SCOPE = re.compile(
    r"\b(?:proses|process)\b\s*(?P<value>.*)$",
    re.IGNORECASE,
)


def normalize_spoken_text(text: str) -> str:
    simplified = _NON_WORD.sub(" ", text.lower())
    return _SPACE.sub(" ", simplified).strip()


def _scope_for(text: str, pattern: re.Pattern[str]) -> tuple[str, bool]:
    match = pattern.search(text)
    if match is None:
        return text, True
    return match.group("value").strip(), False


def _contains_phrase(text: str, phrase: str) -> bool:
    if not phrase:
        return False
    return re.search(rf"(?<!\w){re.escape(phrase)}(?!\w)", text) is not None


def _find_matches(
    text: str,
    vocabulary: Mapping[str, tuple[str, ...]],
    *,
    scope: str,
    fallback_scope: bool,
) -> list[VocabularyMatch]:
    normalized_text = normalize_spoken_text(text)
    matches: list[VocabularyMatch] = []

    for canonical, aliases in vocabulary.items():
        candidates = (canonical, *aliases)
        best_alias: str | None = None
        best_score = 0.0
        for alias in candidates:
            normalized_alias = normalize_spoken_text(alias)
            if not _contains_phrase(normalized_text, normalized_alias):
                continue
            if normalized_text == normalized_alias:
                score = 1.0
            elif fallback_scope:
                score = 0.82
            else:
                score = 0.94
            if best_alias is None or score > best_score or (
                score == best_score and len(normalized_alias) > len(normalize_spoken_text(best_alias))
            ):
                best_alias = alias
                best_score = score
        if best_alias is not None:
            matches.append(
                VocabularyMatch(
                    canonical=canonical,
                    alias=best_alias,
                    confidence=best_score,
                    scope=scope,
                )
            )

    return sorted(matches, key=lambda item: (-item.confidence, item.canonical))


class JobContextNormalizer:
    """Turn a constrained operator transcript into reviewable material/process metadata."""

    def __init__(
        self,
        vocabulary: JobVocabulary | None = None,
        *,
        min_transcript_confidence: float = 0.55,
    ) -> None:
        if not 0 <= min_transcript_confidence <= 1:
            raise ValueError("min_transcript_confidence must be between 0 and 1")
        self.vocabulary = vocabulary or default_job_vocabulary()
        self.min_transcript_confidence = min_transcript_confidence

    def normalize(self, transcript: Transcript | str) -> JobContextResult:
        if isinstance(transcript, str):
            transcript = Transcript(text=transcript)

        normalized = normalize_spoken_text(transcript.text)
        material_scope, material_fallback = _scope_for(normalized, _MATERIAL_SCOPE)
        process_scope, process_fallback = _scope_for(normalized, _PROCESS_SCOPE)

        material_matches = _find_matches(
            material_scope,
            self.vocabulary.materials,
            scope="whole_transcript" if material_fallback else "material",
            fallback_scope=material_fallback,
        )
        process_matches = _find_matches(
            process_scope,
            self.vocabulary.processes,
            scope="whole_transcript" if process_fallback else "process",
            fallback_scope=process_fallback,
        )

        issues: list[str] = []
        material_match: VocabularyMatch | None = None
        process_match: VocabularyMatch | None = None

        if len(material_matches) == 1:
            material_match = material_matches[0]
        elif not material_matches:
            issues.append("material_missing")
        else:
            issues.append("material_ambiguous")

        if len(process_matches) == 1:
            process_match = process_matches[0]
        elif not process_matches:
            issues.append("process_missing")
        else:
            issues.append("process_ambiguous")

        if (
            transcript.confidence is not None
            and transcript.confidence < self.min_transcript_confidence
        ):
            issues.append("transcript_low_confidence")

        ready = material_match is not None and process_match is not None and not issues
        return JobContextResult(
            transcript=transcript.text,
            material=material_match.canonical if material_match else None,
            process=process_match.canonical if process_match else None,
            transcript_confidence=transcript.confidence,
            material_match=material_match,
            process_match=process_match,
            issues=tuple(issues),
            ready=ready,
        )


class FasterWhisperTranscriber:
    """Optional offline-first faster-whisper adapter for local operator-note transcription."""

    def __init__(
        self,
        model_name_or_path: str = "small",
        *,
        device: str = "cpu",
        compute_type: str = "int8",
    ) -> None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise RuntimeError(
                "faster-whisper is required for local transcription. Install FactoryLens "
                "with the speech extra: python -m pip install -e '.[speech]'"
            ) from exc

        self.model_name_or_path = model_name_or_path
        self._model = WhisperModel(
            model_name_or_path,
            device=device,
            compute_type=compute_type,
        )

    def transcribe(self, audio_path: str | Path, *, language: str | None = "id") -> Transcript:
        segments, info = self._model.transcribe(
            str(audio_path),
            language=language,
            vad_filter=True,
        )
        collected = list(segments)
        text = " ".join(segment.text.strip() for segment in collected if segment.text.strip())

        weighted_logprob = 0.0
        total_weight = 0.0
        for segment in collected:
            duration = max(float(segment.end) - float(segment.start), 0.01)
            weighted_logprob += float(segment.avg_logprob) * duration
            total_weight += duration
        confidence = None
        if total_weight > 0:
            confidence = min(max(math.exp(weighted_logprob / total_weight), 0.0), 1.0)

        detected_language = getattr(info, "language", language)
        return Transcript(
            text=text,
            language=detected_language,
            confidence=confidence,
        )
