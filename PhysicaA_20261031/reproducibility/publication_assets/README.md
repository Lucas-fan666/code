# Current journal figure sources

These scripts use the retained data and summaries in this folder. They reproduce native vector artwork and data visualizations; no propagation experiments are run.

From this folder, install `python -m pip install -r requirements-figures.txt`. Inkscape is additionally required to export the mechanism SVG to PDF. Run `python tools/redraw_jcs_figures.py` to redraw the five current overview/runtime/scaling/search panels. Outputs are written to `source/` and `visualization/exports/`.

To rebuild only current Figure 2, run `python -c "from tools.redraw_jcs_figures import runtime; runtime()"`.

The remaining inherited study figures use the original plotting programs in their study folders. The exact PDFs submitted with the article are in the separate JCS figure/source archives. Plotting scripts and inputs are retained; PDF file hashes may vary with rendering software versions and metadata.

## Final panel typography

The final manuscript uses lowercase parenthesized bold panel identifiers at 9 pt at the placed size. The native mechanism generator supplies its matching labels and separates the intersection/union annotations from node numbers. A single-panel forest does not need an `(a)` identifier.

The typography pass preserves existing PDF drawing paths and numerical text. After exporting the figures, place the 17 current figure PDFs from the editable LaTeX archive in `source/`, then run:

```bash
python tools/standardize_panel_labels.py --source-dir source --main-tex /path/to/main.tex --supplement-tex /path/to/supplement.tex --manifest panel_labels.json
```

Use the current main and supplementary LaTeX files because the placed figure widths determine the required font size. The formatter does not redraw measured data or change the study source/configuration hashes. The SVG mechanism is generated directly with its final typography.

## Figure terminology

Current Figure 4 headings are `FEX vs NEX` and `FEX vs greedy`. Current Figure 3 uses `RTC (global)` for the global common-reaction-path comparator, matching Table 3; `Incremental RTC` in Figure 2 denotes the incremental implementation. After exporting the figures, synchronize these vector text labels without changing numerical values or drawing paths:

```bash
python tools/harmonize_figure_terminology.py --source-dir source --manifest figure_terminology.json
```
