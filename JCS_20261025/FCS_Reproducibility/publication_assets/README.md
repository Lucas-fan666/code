# Current journal figure sources

These scripts use the retained data and summaries in this folder. They reproduce native vector artwork and data visualizations; no propagation experiments are run.

From this folder, install `python -m pip install -r requirements-figures.txt`. Inkscape is additionally required to export the mechanism SVG to PDF. Run `python tools/redraw_jcs_figures.py` to redraw the five current overview/runtime/scaling/search panels. Outputs are written to `source/` and `visualization/exports/`.

To rebuild only current Figure 2, run `python -c "from tools.redraw_jcs_figures import runtime; runtime()"`.

The remaining inherited study figures use the original plotting programs in their study folders. The exact PDFs submitted with the article are in the separate JCS figure/source archives. Plotting scripts and inputs are retained; PDF file hashes may vary with rendering software versions and metadata.
