# RTSP Operator Voice Notes

FactoryLens can capture a short operator voice note from the **audio track exposed by an RTSP camera**. This is the second half of the human-to-machine metadata interaction:

```text
three-finger gesture
        ↓
operator-note session
        ↓
RTSP camera microphone
        ↓
FFmpeg audio capture
        ↓
local WAV evidence
        ↓
operator_note_captured event
        ↓
future speech-to-text + material/process normalizer
```

This feature does not send commands to the CNC. It records operator metadata only.

## Why FFmpeg instead of OpenCV?

OpenCV is used for camera frames, but its normal video-capture/write path is not the right abstraction for preserving and controlling an RTSP audio track. FactoryLens therefore keeps audio capture behind an FFmpeg adapter.

The initial capture profile is intentionally speech-oriented:

- mono;
- 16 kHz sample rate;
- PCM 16-bit WAV;
- maximum duration 120 seconds;
- optional early stop after detected silence.

That format is simple to inspect and suitable as input to later offline speech-to-text adapters.

## Requirements

Install FFmpeg on the machine running FactoryLens and confirm it is visible on `PATH`:

```bash
ffmpeg -version
```

Keep the real RTSP credential outside the repository:

```bash
export FACTORYLENS_RTSP_URL='rtsp://USERNAME:PASSWORD@CAMERA_IP:554/stream1'
```

## Capture a voice note

```bash
factorylens capture-operator-note \
  --machine-id cnc-03 \
  --source-id cnc-03-spindle \
  --max-seconds 120 \
  --silence-seconds 3 \
  --start-grace-seconds 10
```

If `--output` is omitted, the WAV file is stored under `data/operator-notes/`, which is ignored by Git.

At the end, the command prints an `operator_note_captured` Machine Event containing credential-redacted source metadata and an audio evidence path.

## Silence stop

By default, FactoryLens asks FFmpeg to detect about 3 seconds of silence. A startup grace period prevents the capture from immediately closing while the operator is moving into position or preparing to speak.

Disable early silence stop and rely only on the 120-second ceiling:

```bash
factorylens capture-operator-note --silence-seconds 0
```

Silence detection is environment-dependent. CNC spindle noise, coolant, compressed air and neighboring machines can keep the acoustic level above the threshold even after the operator stops speaking. Treat the default threshold as a starting point, not a universal setting.

## Recommended operator phrase

For the first prototype, use a controlled sentence instead of unrestricted narration:

```text
Bahan S45C. Proses penghalusan.
```

or:

```text
Material SUS304. Process drilling.
```

A later speech-to-text/normalization layer will map speech variants such as `es empat lima ce` to a configured canonical material such as `S45C`.

## Camera audio validation

Before connecting gesture → voice note automatically, validate the actual camera microphone:

1. capture a 10 to 20 second note with the CNC idle;
2. play the WAV locally and confirm speech intelligibility;
3. repeat with spindle/coolant conditions representative of production;
4. confirm the camera enclosure or acrylic protection does not block the microphone opening;
5. compare operator distance and speaking direction;
6. verify FFmpeg reports a usable audio stream;
7. tune silence threshold/grace only after listening to real samples.

If the RTSP source exposes video but no usable audio track, FactoryLens raises a clear audio-capture error instead of silently producing an empty note.

## Credential safety

FFmpeg may echo input URLs in diagnostic output. FactoryLens sanitizes RTSP URLs before including FFmpeg diagnostics in raised errors. The raw RTSP URL is never written into the Machine Event.

Still follow the stronger rule: **never paste real RTSP usernames/passwords into GitHub issues, commits, screenshots or public logs.**

## Next milestone

The captured WAV becomes input to the speech layer:

```text
operator_note.wav
      ↓
offline speech-to-text
      ↓
"bahan es empat lima ce proses penghalusan"
      ↓
controlled-vocabulary normalizer
      ↓
material = S45C
process  = finishing
```

That work is tracked separately so audio capture remains replaceable and testable.
