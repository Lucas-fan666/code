#!/usr/bin/env python3
"""Install prevalidated mixed raster/vector Figure 1 masters."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[1]
src=root/'figure_source'; out=src/'artwork'; out.mkdir(exist_ok=True)
for ext in ('pdf','svg','png'):
    shutil.copy2(src/f'fig1_master.{ext}',out/f'Fig1.{ext}')
for ext in ('pdf','png'):
    shutil.copy2(src/f'fig1_master.{ext}',root/'manuscript'/f'fig1.{ext}')
print('Installed Figure 1 master assets')
