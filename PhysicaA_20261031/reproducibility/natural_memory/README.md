# Natural-history memory study

Run `python3 run.py` then `python3 analyze.py` from this directory (or use absolute paths). Requires Python, NumPy, Matplotlib and g++ supporting C++17. The original design and source hashes are checked before execution. Do not edit the locked files to accommodate results.

The study uses 32 new graphs in four families and two uncontrolled prehistories each, including extinction. Histories start at 10 R, 10 C, 80 U and A=0, evolve for two time units at lambda=.2, then branch with the same node state and targets. Continuations use lambda .02,.2,2; dynamic natural, dynamic reset, frozen natural and zero-memory variants; no control and top-four R-degree with deterministic degree filling when fewer than four R nodes exist. Control u=3, D=2; loss window H=10. There are 98,304 continuation trajectories and 64 prehistory trajectories. Frozen and zero conditions are repeated on the shared tapes for each lambda as internal controls; these are physical calls, not independent extra replicates.

The engine is an instrumented copy of the existing reset-tape engine, with terminal x,A returned for histories. It continues after rumor extinction to track memory. The first context's loss outputs are checked against the old loss-only routine. Raw traces, losses, topology, initial states, memories, targets and continuation tape identifiers are in graph_*.npz. Generation seeds are deterministic functions specified in run.py and design.json.

All summaries are descriptive. Graph-stratified bootstrap intervals are pointwise, not a multiple-testing confirmation family. The two histories and all settings stay within their graph when resampled. No graph is omitted for extinction or an unfavorable effect.

For dynamic natural versus dynamic reset, the mean-memory contrast at each time is decomposed into exp(-lambda*t)*mean(A0) and a residual. The exact variation-of-constants identity identifies this residual as accumulated differences in the state-driven memory inputs. This does not by itself estimate a rebound probability or prove long-time persistence. Signed spatial means can cancel heterogeneous face responses.
