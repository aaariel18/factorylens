# Speech-to-Text and Job Context

FactoryLens turns an operator voice note into **reviewable, structured job metadata**. The system is intentionally conservative: if material or process is missing, ambiguous, or the transcript is low-confidence, the result is **not ready** and must not silently arm the next machine-cycle workflow.

## Target operator phrase

For the first CNC prototype, use a short controlled sentence:

```text
Bahan S45C. Proses penghalusan.
```

FactoryLens normalizes that to:

```json
{
  "material": "S45C",
  "process": "finishing",
  "ready": true
}
```

The raw transcript and the alias that matched are preserved so operators/developers can audit why the normalization happened.

## Spoken aliases

Speech recognition may transcribe part codes phonetically. The starter vocabulary therefore includes variants such as:

```text
"es empat lima ce"  -> S45C
"sus tiga nol empat" -> SUS304
"es ka de sebelas" -> SKD11
"penghalusan" -> finishing
"pengasaran" -> roughing
"pengeboran" -> drilling
```

The built-in vocabulary is only a starter. Each factory should maintain its own controlled list of materials and process names rather than letting a language model invent values.

## Test the normalizer without speech recognition

```bash
factorylens normalize-job-text \
  "bahan es empat lima ce proses penghalusan" \
  --confidence 0.91 \
  --machine-id cnc-03
```

When both required fields are unambiguous, the command prints a normalized result and then a `job_context_set` Machine Event.

If the phrase is ambiguous:

```bash
factorylens normalize-job-text \
  "bahan S45C atau SUS304 proses finishing"
```

FactoryLens returns `ready: false`, reports `material_ambiguous`, and exits non-zero. It does **not** choose one material on the operator's behalf.

## Offline-first transcription

The first optional adapter uses `faster-whisper` locally:

```bash
python -m pip install -e ".[speech]"
```

Then transcribe a WAV captured by FactoryLens:

```bash
factorylens transcribe-operator-note \
  data/operator-notes/cnc-03_YYYYMMDD_HHMMSS.wav \
  --model small \
  --language id \
  --machine-id cnc-03
```

`--model` may be a faster-whisper model name or a local model directory. For genuinely disconnected factory operation, pre-stage the model files on the PC and point `--model` to that local directory. Do not depend on an internet download during production.

## Confidence

The speech adapter exposes an approximate transcript confidence derived from segment log probabilities. This number is useful as a **review gate**, not a calibrated probability of correctness.

The default normalizer rejects a transcript confidence below `0.55` by adding:

```text
transcript_low_confidence
```

The material/process matcher also surfaces how it matched:

- exact scoped alias: strongest deterministic match;
- alias within the expected `bahan/material` or `proses/process` scope: strong match;
- whole-transcript fallback: weaker match.

## Separation of responsibilities

```text
WAV evidence
   ↓
SpeechToText adapter
   ↓ Transcript(text, language, confidence)
JobContextNormalizer
   ↓ JobContextResult
review gate: ready?
   ↓ yes only
JOB_CONTEXT_SET event
```

The normalizer does not start the CNC. A later machine-cycle trigger consumes already-approved job context and separately observes controller/PLC state.

## Field validation

Before relying on speech metadata:

1. complete RTSP microphone validation using real shop-floor noise;
2. collect representative phrases for every material/process expected in the pilot;
3. run each phrase multiple times and record transcript variants;
4. extend aliases only from observed variants, not guesses;
5. measure material/process false acceptance separately from transcription errors;
6. keep a manual review path for missing/ambiguous/low-confidence results;
7. benchmark the chosen Whisper model on the actual CPU;
8. keep audio and transcripts local if they contain production-sensitive information.

## Privacy and safety

Operator audio can contain personal or production-sensitive information. FactoryLens should capture only the short note needed for job context and retain it according to the site's policy.

Speech metadata is operational context only. It must never bypass guarding, interlocks, CNC program validation, emergency stops or safety PLC functions.
