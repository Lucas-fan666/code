# Persistent-topology replay confirmation

The immutable lock is `locked.json`; its SHA-256 is recorded in `locked.sha256`. Source and analysis hashes were fixed before confirmation. The original project sources and all older observations are unchanged.

32 new graphs, three unconditioned histories per graph, sizes 100/300, four families. Each complete greedy-plus-FEX search charges exactly 1,024 marginal continuations. The persistent comparator constructs topology once per search and uses one full-prefix native call per stage. Creation/free, candidate creation, inference and tracing are timed. Compilation, graph/prehistory, final evaluation and file serialization are excluded. No outcomes are discarded.

From the project root:

```bash
python publication_revision/optimized_replay/test_backend.py
python publication_revision/optimized_replay/analyze.py
python publication_revision/plot_confirmation.py
```

The second command performs offline raw-mean, budget and complete decision replay validation and recomputes the two Bonferroni-adjusted comparisons. It does not run new propagation. To generate an independent timing rerun, first copy the study and remove only that copy's `results` directory, then run `run.py`; original retained timing data should not be overwritten. Wall times vary by machine.

Persistent replay/local ratio: 3.790121 [3.386896,4.195307], 31 positive/one negative graph. Fixed batching/local: 1.001328 [0.893950,1.107776], 16/16 signs. The latter does not pass. All 288 decisions are replayed, and all 96 persistent/fixed transcripts match exactly. Local batching has the same joint distribution under the theorem assumptions, without an identical integer-seed realization requirement.
