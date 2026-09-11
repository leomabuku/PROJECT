"""PyInstaller entry point for the TongaLang desktop IDE."""

from pathlib import Path
import sys


# Running this source file directly places ``distribution`` rather than the
# repository root on sys.path. Keeping the entry point runnable makes packaging
# failures easier to diagnose and gives PyInstaller the same import layout.
if not getattr(sys, "frozen", False):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gui.app import TongaLangGUI, main


def _smoke_test() -> None:
    """Create the packaged UI once so release builds can be verified safely."""
    import tkinter as tk

    root = tk.Tk()
    try:
        application = TongaLangGUI(root)
        root.update_idletasks()
        if not application.editor.winfo_exists():
            raise RuntimeError("The TongaLang editor did not initialize.")
    finally:
        root.destroy()


if __name__ == "__main__":
    if "--smoke-test" in sys.argv:
        _smoke_test()
    else:
        main()
