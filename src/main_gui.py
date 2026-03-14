#!/usr/bin/env python3
"""GUI entry point for MTG Cart Order Parser."""

import sys
import tkinter as tk
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.gui.app import MTGOrderParserGUI


def main():
    root = tk.Tk()

    icon_path = Path(__file__).parent.parent / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except Exception:
            pass

    app = MTGOrderParserGUI(root)
    app.run()


if __name__ == "__main__":
    main()
