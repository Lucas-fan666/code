#!/usr/bin/env python3
"""Render every redesigned KAIS quantitative figure (Fig2-Fig8) in one pass.

Figure 1 is a hand-built conceptual raster schematic and is intentionally left
untouched. All data values and claims are identical to the archived tables;
only the visual design is upgraded.
"""
import pro_style as S
import pro_redraw as a
import pro_redraw2 as b
import pro_redraw3 as c

if __name__ == '__main__':
    S.apply()
    print('Rendering all redesigned quantitative figures...')
    a.fig_budgets()
    a.fig_samplers()
    a.fig_ranks()
    b.fig_heterogeneity()
    b.fig_candidates()
    c.fig_factorial()
    c.fig_sequential()
    print('All figures (Fig2-Fig8) written to artwork/ and manuscript/.')
