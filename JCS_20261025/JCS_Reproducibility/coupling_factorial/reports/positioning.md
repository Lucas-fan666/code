# Scope and nearest-work check (21 October 2026)

Primary sources checked:

- Gupta, Joshi and Yagan, Best-Arm Identification in Correlated Multi-Armed
  Bandits, https://arxiv.org/abs/2109.04941 . This method already uses known
  conditional-reward bounds to infer about unsampled arms. Side information
  for unobserved alternatives is not a new general principle here.
- Saad, Blanchard and Verzelen, Covariance Adaptive Best Arm Identification,
  https://arxiv.org/abs/2306.02630 and NeurIPS 2023 proceedings,
  https://papers.neurips.cc/paper_files/paper/2023/hash/e82ef7865f29b40640f486bbbe7959a7-Abstract-Conference.html . Simultaneous dependent arm observations and covariance adaptation are established.

The new implementation is therefore an order-derived auxiliary-oracle
construction for this process, not a new generic correlated race. Its
one-sided screen can also use RTC endpoint contrasts: the new 2x2 study gives
that comparator exactly the same structural oracle. No comparison with an
adapted C-LUCB implementation or exhaustive algorithm class is claimed.

The chord/Hoeffding calculation and stopped-positive-drift argument are
applications of elementary established inequalities, not new concentration
principles. Their role is to express sufficient screening cost in terms of
the endpoint mean and support, and to distinguish graphical nonnegative
support from exact signed alternatives. The fixed-reservation break-even
condition is not an equal-total-cap theorem for the evaluated implementation.

An implicit action-region certificate is a direct proved corollary of the
uniform endpoint bracket. It is not a claim of an exponential runtime speedup
or a new empirical result. Adaptive regions require fresh tapes after proposal
and summable error allocations. The current code tests only a fixed region.

The earlier user instruction restricting manuscript references to the existing
ref.bib is retained: the verified external records above remain in this report.
Their omission from the manuscript bibliography remains a literature-positioning
limitation to resolve before a formal submission; no imaginary entry is added.

The zero-width lower bound is a rare-contamination / transcript argument for a distribution-free black-box diameter screen. It does not establish optimality for this network model, for candidate-query algorithms or for states where exact reasoning gives the answer without simulation. It is presented as a restricted comparison with a matching sampling order, not a new general testing lower-bound technique.

The signed-class companion bound uses a symmetric two-point reference and a likelihood-ratio/Jensen argument. Its quadratic small-tolerance order describes that unrestricted signed oracle class, not a lower bound for the actual RTC implementation. Both oracle lower bounds assume almost-sure rejection at the stated reference law; the finite capped implementation can instead return unresolved.
