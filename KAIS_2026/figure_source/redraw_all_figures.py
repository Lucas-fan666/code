#!/usr/bin/env python3
"""Install selected schematic and redraw quantitative assets Fig2–Fig7; Fig8 has a separate sequential exporter."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('redraw_revision.py')),run_name='__main__')
