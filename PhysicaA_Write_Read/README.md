# Writing, retention and dynamical readout of group memory

This branch contains all 41 Python and 8 C++ scientific source files from the
self-contained replication archive, together with the fixed simulation and
analysis configurations. `SOURCE_MANIFEST_SHA256.json` records their SHA-256
hashes and sizes. The source members match those in the revised replication archive.

## Reproduce from the saved data

Unpack `PhysicaA_Code_Data_Revision_20261106.zip`, enter
`PhysicaA_Memory_Write_Read`, and run:

```bash
python -m pip install -r requirements.txt
python reproduce.py --from-data
```

The full workflow requires Python, a C++17 compiler, Cairo, pdflatex and bibtex.
The complete archive supplies the results, seeds, realized topologies, fonts,
manuscript sources and other inputs used by this workflow. The GitHub mirror
provides the scientific code and configurations; the data and document assets
are distributed in the complete archive for Zenodo.

## Source layout

- `reproducibility/run.py`, `engine_api.py`, `batched.cpp` and `engine/`:
  simulation driver, coupled kernels and wrappers.
- `reproducibility/analyze.py`, `dense_*.py`, `reviewer_*.py` and
  `interpretation*.py`: fixed analyses, grid extension, strength and school
  extensions, and mechanism summaries.
- `reproducibility/verify.py` and validation scripts: exhaustive finite-state
  identities, exact frozen-memory checks, kernel replay and result validation.
- `reproducibility/vendor/src/`: retained simulation dependencies.
- `figures/`: publication figure scripts and mechanism definitions.
- `manuscript/build.py`: document build entry point used by the full archive.
- `reports/legacy_plotting.py`: archived plotting source.

To run the data-independent deterministic checks with NumPy, SciPy and a C++17
compiler installed:

```bash
python reproducibility/verify.py
```

## Recover the self-contained archive

The saved original `PhysicaA_Code_Data_Write_Read.zip` has SHA-256
`d247bdebb1af487880ebb2357dd1f66cb24849a07af358720f681f02efca9ed2`.
The included utility recovers 64 strength-analysis inputs from its merged arrays
and verifies all 102 original result-file hashes:

```bash
python restore_zenodo_archive.py PhysicaA_Code_Data_Write_Read.zip
```

It writes `PhysicaA_Zenodo_Code_Data_Recovered.zip` beside the input. ZIP byte
hashes can differ between builds because of archive metadata; the original
result hashes and recovered loss/dose arrays are checked directly. The utility
has an independent synthetic-data smoke test.

The two school datasets supply fixed contact structures for synthetic spreading
dynamics. Their public sources, preprocessing rules and source hashes are
documented in `reproducibility/inputs/topology_provenance.json` and the complete
archive. Archive DOI: https://doi.org/10.5281/zenodo.23811459.

## Short-time response verification

The deterministic checker also compares the leading quadratic occupation-response coefficient with exact reward matrix exponentials for 243 single-triangle cases. These additional checks use frozen memory and introduce no new study trajectories. The general fixed-rate expansion and its proof are in the article and Supplementary Material. Figure labels distinguish retention relaxation from the initial occupation-response drift.
