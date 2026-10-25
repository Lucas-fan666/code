# Complete source and retained evidence

Extract the code and Core_Search_Data archives into the same parent. Their paths merge into `FCS_Reproducibility`. Install Python 3.12, g++ with C++17, and `pip install -r requirements-lock.txt`. From that directory run:

```bash
python publication_revision/reproduce_revision.py
```

This reconstructs both complete-search comparisons, validates raw means, budgets and stored decisions, recreates the optimized replay figure and recomputes the legacy RTC/robustness summaries. It runs no new confirmatory propagation. The new persistent-replay cohort comprises 32 graphs x 3 histories, 288 searches and 294,912 online marginal continuations. Both primary and unfavorable secondary comparisons are retained.

The other study folders contain their locked source, configurations, analysis and validation scripts. Their raw observations are split across three optional module data archives: Early_Certificate_Data, Refined_Certificate_Data and Portfolio_Extension_Data. Extract these into the same parent to reproduce those modules. Run their original reproduction entry points separately to regenerate the earlier selection/scaling studies. Timing reruns should use a separate copy and fresh result directory, preserving archived measurements. Wall times depend on hardware and compilation.

The legacy WP0--WP9 compact archive preserves original code, configurations, numeric summaries and validation. It does not contain every original historical stochastic trajectory. Derived-CSV recomputation is labeled as such and is not presented as raw-loss replay or new simulation. No original raw file or locked source is modified by the manuscript revision.

The LaTeX source archive is separate. No private credentials, downloaded helper scripts, cached binaries, duplicate manuscript versions or intermediate image montages are included. GitHub uploading remains deferred.
