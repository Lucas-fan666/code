# Writing, retention and dynamical readout of group memory in higher-order spreading

This archive contains the simulation and analysis sources, fixed protocols,
saved seeds, realized topologies, all raw results, figure code and manuscript
sources for the study.

The central observable compares different pulse-written memory fields on an
identical complete withdrawal node configuration. The analysis connects the
written load, its accessibility through eligible donor configurations, and
the subsequent occupation response under competing relaxation scales.

The 100-pair grid includes 34 original, 34 dense-grid and 34 robustness or
school-extension result files. The 64 strength-analysis inputs were recovered
from the loss and dose arrays in the corresponding merged result files. The
recovery checks all 102 original-result SHA-256 hashes and performs no new
simulation.

To reproduce the article from the saved data, unpack this archive, enter the
PhysicaA_Memory_Write_Read directory and run:

    python -m pip install -r requirements.txt
    python reproduce.py --from-data

The workflow also needs a C++17 compiler, Cairo, pdflatex and bibtex.
The two school datasets provide contact structures for synthetic spreading
dynamics; their source, preprocessing rule and hashes are documented under
reproducibility/inputs/. Third-party asset and font licenses accompany their
files. Archive DOI: https://doi.org/10.5281/zenodo.23811459.

## Current response-onset check

The article now states the leading quadratic short-time occupation response.
Run `python reproducibility/verify.py` for the local generator identities,
occupation bounds, kernel replay and 243 additional exact short-time checks.
The additional cases use frozen-memory matrix exponentials, with no new study
trajectories. The full fixed-rate expansion is proved in the article and
Supplementary Material. Main figures distinguish retention relaxation from the
initial occupation-response drift. Detailed strength sensitivity is in the
Supplementary Material.
