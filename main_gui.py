#!/usr/bin/env python3
"""
GUI entry point for MTG Card Kingdom Order Parser.

This script launches the Tkinter-based graphical user interface
for parsing Card Kingdom cart HTML and generating Excel orders.

Usage:
    python main_gui.py
"""

import sys
import tkinter as tk
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.app import MTGOrderParserGUI


def main():
    """Launch the GUI application."""
    root = tk.Tk()
    
    # Set application icon if available
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        try:
            root.iconbitmap(str(icon_path))
        except:
            pass  # Icon not critical
    
    # Create and run app
    app = MTGOrderParserGUI(root)
    app.run()


if __name__ == '__main__':
    main()