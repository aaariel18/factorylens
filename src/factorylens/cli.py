from __future__ import annotations

import argparse
from pathlib import Path

from .session import MachineSession


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


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "demo-event":
        return run_demo(args)
    raise AssertionError(f"unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
