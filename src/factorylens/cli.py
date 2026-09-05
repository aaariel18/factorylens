from __future__ import annotations

import argparse
import os
from pathlib import Path

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


def run_validate_rtsp(args: argparse.Namespace) -> int:
    uri = args.source or os.environ.get(args.source_env)
    if not uri:
        raise SystemExit(
            f"RTSP source missing. Set {args.source_env} or pass --source. "
            "Environment variables are recommended for credentials."
        )

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


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "demo-event":
        return run_demo(args)
    if args.command == "validate-rtsp":
        return run_validate_rtsp(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
