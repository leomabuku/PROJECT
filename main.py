from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tongalang.runner import safe_run_file


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tongalang",
        description="Run TongaLang .tg source files.",
    )

    parser.add_argument(
        "file",
        nargs="?",
        help="Path to the TongaLang .tg file to run.",
    )

    parser.add_argument(
        "--max-loop",
        type=int,
        default=10000,
        help="Maximum loop iterations before TongaLang stops a loop. Default: 10000.",
    )

    parser.add_argument(
        "--max-call-depth",
        type=int,
        default=250,
        help="Maximum nested function calls before TongaLang stops recursion. Default: 250.",
    )

    parser.add_argument(
        "--version",
        action="store_true",
        help="Show TongaLang version.",
    )

    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.version:
        from tongalang import __version__

        print(f"TongaLang {__version__}")
        return 0

    if not args.file:
        print("TongaLang runner")
        print()
        print("Usage:")
        print("  python main.py path/to/file.tg")
        print()
        print("Examples:")
        print("  python main.py examples/01_mazyina.tg")
        print("  python main.py examples/03_kuinduluka_kufumbwa.tg")
        print()
        print("Mulubizyo: Kunyina fayilo yapeegwa.")
        print("Error: No input file was provided.")
        return 1

    file_path = Path(args.file)

    success = safe_run_file(
        file_path,
        max_loop_iterations=args.max_loop,
        max_call_depth=args.max_call_depth,
    )

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
