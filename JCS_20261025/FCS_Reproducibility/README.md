# Monotone Coupling and Joint Simulation for Higher-Order Networks with Memory

Reproducibility code for the Journal of Computational Science manuscript by Junkai Fan. Release: 25 October 2026.

Zenodo DOI: https://doi.org/10.5281/zenodo.23622583
Versioned code: https://github.com/Lucas-fan666/code/tree/jcs-submission-20261025/JCS_20261025

## Setup and full offline reconstruction

Use Python 3.12 and g++ with C++17 support. Install `python -m pip install -r requirements-lock.txt`. The release was checked using Python 3.12.14 and the pinned package versions.

Download these four data files from the accompanying Zenodo deposit and extract them into the **parent** of this directory, retaining their `FCS_Reproducibility/` paths:

- `JCS_Core_Search_Data.zip`
- `JCS_Early_Certificate_Data.zip`
- `JCS_Refined_Certificate_Data.zip`
- `JCS_Portfolio_Extension_Data.zip`

The historical directory name `FCS_Reproducibility` is retained so locked configurations and source hashes remain valid. From this directory run:

```bash
python reproduce_all.py
```

This runs the existing simulator/selector tests, reconstructs 768 complete searches and 288 persistent-topology comparisons from retained losses, and replays all 1,440 decisions from five supplementary studies. It verifies seeds, requested action lists, stopping/certification events, selected indices and copy accounting, then reruns the original analyses and checks their numerical agreement with the stored summaries. Stored wall times are analyzed as observations; they are not regenerated. No new confirmatory propagation experiment is performed.

For supplementary results alone run `python reproduce_supplement.py`; select a study with `--module envelope_selection`, `coupling_factorial`, `witness_selection`, `adaptive_screening` or `portfolio_validation`. Reports are written to `reproducibility_reports/`.

## Contents and scope

- `src/`, `vendor/src/`: exact simulation, graph generation and certificate engines.
- `end_to_end_search/`, `publication_revision/optimized_replay/`: main complete-search comparisons.
- `envelope_selection/`, `coupling_factorial/`, `witness_selection/`, `adaptive_screening/`, `portfolio_validation/`: supplementary studies, locked source, configurations and analyses.
- `publication_assets/`: current journal plotting scripts and retained plotting inputs; see its README for extra dependencies.
- `protocol/`: earlier runtime and scaling configurations.
- `review_inputs/` and the Zenodo-only `legacy/` compact archive: inherited numeric evidence and source. Their derived-CSV recomputations are not represented as replay of unretained historical stochastic trajectories.

The four data archives provide retained observations for the two complete-search cohorts and the five supplementary cohorts. Earlier WP0--WP9 material is a compact archive of code, configurations, derived tables and checks; not every historical propagation trajectory is retained. `publication_revision/reproduce_revision.py` is an additional historical reconstruction entry point and requires the full code archive, including the compact legacy ZIP and its textual provenance input, from Zenodo.

Legacy `reproduce_*.py` entry points can also regenerate studies or edit older manuscript trees. Use the current `reproduce_all.py` or `reproduce_supplement.py` for offline replay of this release. Rerun timed simulations only in a separate copy and fresh result directories. Performance depends on hardware and compiler.

## Unchanged locked sources

Original study sources, configurations and raw observations retain their archived hashes. The two top-level reproduction entry points and journal plotting assets were added for this release; none changes the frozen selectors or propagation engines. Original release reports remain historical records and can refer to earlier journal layouts.

The DOI was provided by the author. Its public record could not be retrieved during packaging; upload the release files to that record and publish it before relying on public DOI access.
