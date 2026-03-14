#!/usr/bin/env python3
"""CLI entry point for MTG Cart Order Parser."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.cli import cli

if __name__ == "__main__":
    cli()
