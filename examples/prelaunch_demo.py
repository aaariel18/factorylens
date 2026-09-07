from __future__ import annotations

import argparse
from pathlib import Path

from factorylens.prelaunch import run_prelaunch_demo


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the hardware-free FactoryLens pre-launch demo.",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=45.0,
        help="target playback duration in seconds",
    )
    parser.add_argument(
        "--realtime",
        action="store_true",
        help="sleep between steps so the demo plays in real time",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/prelaunch-demo"),
    )
    args = parser.parse_args()

    print("FactoryLens PRE-LAUNCH DEMO")
    print("SIMULATION ONLY — no physical CNC validation is implied.\n")
    result = run_prelaunch_demo(
        output_dir=args.output_dir,
        duration_seconds=args.duration,
        realtime=args.realtime,
    )
    print(f"\nTimeline: {result.timeline_path}")
    print(f"Manifest: {result.manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
