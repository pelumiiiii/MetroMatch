#!/usr/bin/env python3
"""Standalone launcher for Dynamic Metronome application."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.gui.dynamic_metronome import main

if __name__ == "__main__":
    main()
