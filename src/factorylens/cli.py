from __future__ import annotations

import argparse
import os
from datetime import UTC, datetime
from pathlib import Path

from .audio import AudioCaptureConfig, FFmpegRTSPAudioCapture
from .session import MachineSession
from .sources import RTSPSource
from .validation import validate_rtsp_source


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="factorylens",
        description="FactoryLens machine-observability toolkit.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    demo = subparsers.add_parser("demo-event", help="write a small CNC event-sequence demo")
    demo.add_argument("--machine-id", default="cnc-03")
    demo.add_argument("--material", default="S45C")
    demo.add_argument("--process", default="finishing")
    demo.add_argument("--output", type=Path, default=Path("demo-event.jsonl"))

    validate = subparsers.add_parser(
        "validate-rtsp",
        help="run a bounded field validation against a real RTSP camera",
    )
    validate.add_argument(
        "--source",
        help="RTSP URI. Prefer FACTORYLENS_RTSP_URL so credentials stay out of shell history.",
    )
    validate.add_argument(
        "--source-env",
        default="FACTORYLENS_RTSP_URL",
        help="environment variable used when --source is omitted",
    )
    validate.add_argument("--source-id", default="cnc-camera")
    validate.add_argument("--duration", type=float, default=30.0, help="validation seconds")
    validate.add_argument("--max-frames", type=int)
    validate.add_argument(
        "--report",
        type=Path,
        default=Path("data/validation/rtsp-report.json"),
    )
    validate.add_argument("--snapshot", type=Path)
    validate.add_argument("--reconnect-delay", type=float, default=1.0)
    validate.add_argument("--reconnect-attempts", type=int, default=3)

    note = subparsers.add_parser(
        "capture-operator-note",
        help="capture a bounded operator voice note from the RTSP audio track",
    )
    note.add_argument("--machine-id", default="cnc-03")
    note.add_argument("--machine-type", default="cnc_milling")
    note.add_argument("--source-id", default="cnc-camera")
    note.add_argument(
        "--source",
        help="RTSP URI. Prefer FACTORYLENS_RTSP_URL so credentials stay out of shell history.",
    )
    note.add_argument("--source-env", default="FACTORYLENS_RTSP_URL")
    note.add_argument("--max-seconds", type=float, default=120.0)
    note.add_argument(
        "--silence-seconds",
        type=float,
        default=3.0,
        help="stop after this much detected silence; use 0 to disable silence stop",
    )
    note.add_argument("--silence-threshold-db", type=float, default=-35.0)
    note.add_argument("--start-grace-seconds", type=float, default=10.0)
    note.add_argument("--output", type=Path)
    return parser


def run_demo(args: argparse.Namespace) -> int:
    session = MachineSession(args.machine_id, machine_type="cnc_milling")
    events = []
    events.extend(session.trigger_operator_note())
    events.append(session.set_job_context(material=args.material, process=args.process))
    events.append(session.machine_started())
    events.append(session.machine_finished())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(event.to_json(indent=None) + "\n")

    print(f"Wrote {len(events)} events to {args.output}")
    return 0


def _resolve_rtsp_uri(args: argparse.Namespace) -> str:
    uri = args.source or os.environ.get(args.source_env)
    if not uri:
        raise SystemExit(
            f"RTSP source missing. Set {args.source_env} or pass --source. "
            "Environment variables are recommended for credentials."
        )
    return uri


def run_validate_rtsp(args: argparse.Namespace) -> int:
    uri = _resolve_rtsp_uri(args)
    source = RTSPSource(
        uri,
        source_id=args.source_id,
        reconnect_delay_seconds=args.reconnect_delay,
        reconnect_attempts=args.reconnect_attempts,
    )

    with source:
        report = validate_rtsp_source(
            source,
            duration_seconds=args.duration,
            max_frames=args.max_frames,
            snapshot_path=args.snapshot,
        )

    report.write_json(args.report)
    fps_text = "n/a" if report.observed_read_fps is None else f"{report.observed_read_fps:.2f}"
    print(f"RTSP validation complete: {report.frames_read} frames, observed {fps_text} FPS")
    print(f"Source: {report.source_uri}")
    print(f"Report: {args.report}")
    if report.snapshot_path:
        print(f"Snapshot: {report.snapshot_path}")
    return 0


def run_capture_operator_note(args: argparse.Namespace) -> int:
    uri = _resolve_rtsp_uri(args)
    silence_seconds = args.silence_seconds if args.silence_seconds > 0 else None
    config = AudioCaptureConfig(
        max_seconds=args.max_seconds,
        silence_seconds=silence_seconds,
        silence_threshold_db=args.silence_threshold_db,
        start_grace_seconds=args.start_grace_seconds,
    )
    capture = FFmpegRTSPAudioCapture(uri, source_id=args.source_id, config=config)

    output = args.output
    if output is None:
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        output = Path("data/operator-notes") / f"{args.machine_id}_{timestamp}.wav"

    result = capture.capture(output)
    event = result.to_event(args.machine_id, args.machine_type)
    print(event.to_json())
    return 0


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "demo-event":
        return run_demo(args)
    if args.command == "validate-rtsp":
        return run_validate_rtsp(args)
    if args.command == "capture-operator-note":
        return run_capture_operator_note(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
