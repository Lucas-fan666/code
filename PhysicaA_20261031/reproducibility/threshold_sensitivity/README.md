# Threshold sensitivity (post hoc)

Run `python3 reproducibility/threshold_sensitivity/analyze.py` from the extracted package root. Requires Python 3 and NumPy. No simulator is executed. The inputs are retained derived records from the original WP3 study, not newly generated trajectory losses.

All thresholds 0.01, 0.015, 0.02, 0.025, 0.03 are reported for pooled data and all four families. The original 0.02 endpoint, adjusted intervals and gate decision remain unchanged. Stable crossing is determined from the mean estimate at an observed grid point and all larger grid points. `>512` denotes absence of a stable crossing within the grid; it is not extrapolation.

The analysis checks 21,504 context/trial records against 896 graph-level records and reproduces the published pooled means. Inputs, original protocol hash, original analysis, and output lineage are included. `analysis_scope.json` records a post-hoc analysis plan; its hash is an integrity record, not a claim of prospective registration.
