# Group memory and post-intervention response in higher-order spreading

Physica A revision, 31 October 2026. Author: Junkai Fan, Northeastern University.

This release studies synthetic competing-spreading dynamics on synthetic networks and sensor-derived contact topologies. The observed data supply group structure; the rates and outcomes are not observations of misinformation interventions. The memory-mediated fractions refer to the stated paired reset protocol, not an identified causal effect in a population.

## Reproduce this revision

Extract `PhysicaA_Reproducibility_Code.zip` and `PhysicaA_Physical_Response_Data.zip` into the same parent directory. Both create `PhysicaA_20261031`. Then run:

```bash
cd PhysicaA_20261031
python run_physicaA.py
```

This recomputes the new physical-response and precision analyses, redraws the publication figures and builds the main manuscript, supplement and optional single-column copy. Add `--simulate` to rerun the new physical simulations and precision benchmark; add `--skip-pdf` for numerical outputs only. The default command does not rerun all historical experiments.

Requires Python 3, NumPy, SciPy, Matplotlib, g++ with C++17, pdfLaTeX, BibTeX and Inkscape. Versions and the measured environment are recorded in `reports/PhysicaA_Environment.json`. Runtime depends on hardware; the previous natural-history study used about 11 minutes, and new simulation/replay stages are recorded in their logs. No GPU is required.

## GitHub checkout

The branch is `physicaA-submission-20261031` in `Lucas-fan666/code`. Code, protocols and lightweight summaries are under `PhysicaA_20261031`. Large simulation arrays and original data archives are supplied through the release archive. After the assigned Zenodo record is public, `python fetch_physicaA_data.py` retrieves the new physical data and LaTeX source inputs and checks their published checksums. Before publication it reports that the record is unavailable; it does not silently fetch another version.

## Archive identity

The revision has assigned DOI `10.5281/zenodo.23811459`. Its publication status must be checked after upload. The original published record `10.5281/zenodo.23622583` remains the source of the earlier archive files; their byte checksums and renamed export filenames are listed in the release manifest. The new release also includes the original WP0 and WP2-WP7 data/dependency archives recovered from the complete WP1-WP9 package. Historical internal paths retain their original names so locked configurations and checksums remain meaningful; all exported archive filenames use PhysicaA.

## Studies and reporting

- `physicaA_physics`: withdrawal-time state/memory decomposition on eight synthetic and two contact topologies; all 48 triangle cells; weighted four-uniform checks under two drives.
- `physicaA_precision`: threshold-free reference-based MSE, paired variance and cost on four fixed contexts. The finite reference is not an exact oracle. Serial retiming replays identical paths and is not additional independent evidence.
- `natural_memory`, `response_extension`, `physica_a_revision`: earlier descriptive memory studies, supplied with their raw outputs.
- Earlier search, certificate and runtime studies remain in Supplementary Material and the original archives, including inconclusive and unfavorable results.

The new designs were fixed before simulation, with source and configuration SHA-256 files. Results are descriptive. A validation test originally compared nonnested sets as if nested; the correction changes the test and adds the actual intersection, without changing dynamics or selected parameters. The original script and failing log are preserved; the corrected entry point is `physicaA_physics/reproduce.py`. A plot-label escape and publication notation/color-scale adjustments are documented separately. Failed-check arrays were reconstructed from unchanged seeds.

## Numerical lineage and data provenance

Raw losses, endpoint node/memory arrays, seeds, complete time traces and topology arrays are in the per-study NPZ files. CSV summaries and all tested cells are included. No extinction history or unfavorable comparison is removed. All numerical inputs are synthetic except contact topology. The school data come from Austin Benson's simplicial-closure collection, based on Mastrandrea et al. (2015) and Stehlé et al. (2011). We use groups recorded with exactly three members, not every triangle in the aggregate graph. Source descriptions, URLs and checksums accompany the data; third-party data remain subject to their providers' terms.

The main text uses face index sigma, scale T_0, action T_set, expected contrast Delta_SW, background B_g, auxiliary width B_env and horizon K_hor. Archived engines may use earlier variable names; this does not change their parameter values. The proof comparison verifies equality after these explicit notation changes; it is not a new independent mathematical certification.
