from __future__ import annotations

import argparse
from pathlib import Path
import sys
import tkinter as tk

from .gui import TestLabGUI
from .runner import run_test_suite


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the TongaLang visual failure-discovery test laboratory.")
    parser.add_argument("--headless", action="store_true", help="Run without opening the GUI; useful for automation.")
    parser.add_argument("--weakness", action="store_true", help="Run only adversarial weakness probes.")
    parser.add_argument("--autorun", action="store_true", help="Open the GUI and start testing immediately.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    project_root = Path(__file__).resolve().parents[1]
    scope = "weakness" if args.weakness else "all"
    if args.headless:
        result = run_test_suite(project_root, scope=scope)
        coverage = "n/a" if result.coverage_percent is None else f"{result.coverage_percent:.1f}%"
        print(
            f"TongaLang tests: {result.passed}/{result.total} passed, "
            f"{result.failed} failed, {result.skipped} skipped, "
            f"coverage {coverage}, duration {result.duration:.2f}s"
        )
        print(f"Detailed results: {result.artifact_dir}")
        return 0 if result.success else 1

    root = tk.Tk()
    TestLabGUI(root, project_root, autorun=args.autorun)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
