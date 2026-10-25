from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'portfolio_validation'
p=HERE/'protocol/validation_locked.json'
if p.exists():raise RuntimeError('Existing lock is immutable; use a new study for amendments')
old=json.loads((ROOT/'adaptive_screening/protocol/adaptive_locked.json').read_text())
names=list(old['source_sha256'])
names += ['portfolio_validation/baseline.py','portfolio_validation/study.py','portfolio_validation/analyze.py','portfolio_validation/validate.py','portfolio_validation/tests/test_baseline.py','portfolio_validation/theory/baseline_adaptation.md']
c=dict(study='New-graph portfolio stress validation and bounded covariance-adaptive published-method adaptation',locked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='Locked before comparative observations on this cohort',seed_root=202610219863,bootstrap_seed=202610219869,
 families=old['families'],graphs_per_family=8,histories_per_graph_per_cell=1,
 cells=[dict(name='n300_m16_core3',n=300,M=16,overlap='common_three'),dict(name='n100_m32_diverse',n=100,M=32,overlap='diverse_top64')],
 methods=['adaptive_screen','plain','pairwise_eb'],parameters=old['parameters'],selection=old['selection'],routing=old['routing'],evaluation_paths=128,
 portfolio='Top rumor-degree k=4 anchor retained. Core3 cell: next 15 one-swap alternatives. Diverse cell: 31 distinct uniformly sampled 4-subsets from the top64 ranked nodes, with no outcome filtering; intersection may be empty. Rank ties use degree then node ID.',
 prehistory=old['prehistory'],randomization=old['randomization'],accounting=old['accounting'],
 primary='Four planned within-cell wall-cost contrasts: plain/adaptive_screen and pairwise_eb/adaptive_screen in each of the two cells. Each graph is one independent unit; one natural history per cell, paired across methods. Two cells are different stress configurations, not a factorial estimate of individual effects.',
 multiplicity='Bonferroni across four comparisons: central 98.75% family-stratified graph bootstrap intervals, 20000 fixed draws. No pooled superiority claim. All four contrasts reported.',
 quality_gate='All 32 contexts in both compared methods certified at epsilon=.1 and alpha=.05 within unchanged cap32768, and wall-cost ratio adjusted lower bound>1. If either comparator is unresolved, report capped cost and certificate coverage only; do not call it a matched-quality speedup. No successful-query filtering.',
 power='Fixed32 independent graphs per cell,8/family. Approximate80%-power detectable standardized log-cost effect .59 for two-sided98.75% interval. Low power for family-specific superiority and no rare-error calibration claim.',
 scope='One new history per graph/cell controls computational cost; not an exact replication of the prior three-history design. Frozen policy parameters and cap unchanged. New seeds across both cells and prior studies. No changes or selective reruns based on outcomes.',
 external_baseline='Epsilon-PAC adaptation of bounded Pairwise-BAI Algorithm2 no-oversampling variant, Saad et al. NeurIPS2023 arXiv2306.02630v2. Source Section4 radius and allocation unchanged. Same graphical joint oracle and exact extinction presolve. Adaptation documentation and proof frozen. Not an author implementation; no exact identification or Gaussian guarantee claimed.',
 independent_evaluation='128 fresh tapes/action, all methods including unresolved decisions evaluated on same independent matrix; noisy regret relative to minimum estimated mean is descriptive with winner bias, not a true-oracle certificate.',
 bootstrap_resamples=20000,descriptive=['CPU and copies','four graph families','certificate fractions','all capped failures','endpoint routes','independent estimated regret'],source_sha256={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in names})
p.write_text(json.dumps(c,indent=2)+'\n');h=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.sha256').write_text(h+'  validation_locked.json\n');print(h)
