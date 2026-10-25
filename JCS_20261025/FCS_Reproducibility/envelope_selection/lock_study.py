"""Write once, before executing any confirmatory seed or comparison."""
from pathlib import Path
import hashlib,json,datetime
ROOT=Path(__file__).resolve().parents[1];here=ROOT/'envelope_selection'
p=here/'protocol/selection_locked.json'
if p.exists():raise SystemExit('Refusing to overwrite an existing lock')
files=['envelope_selection/selection.py','envelope_selection/study.py','envelope_selection/analyze.py','src/batch_simulator.py','src/batch_engine.cpp','src/graph_generation.py']+[str(x.relative_to(ROOT)) for x in sorted((ROOT/'vendor/src').glob('*.cpp'))]+['vendor/src/simulator.py','vendor/src/set_simulator.py']
cfg=dict(study='Envelope-first finite-portfolio epsilon selection',locked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),status='locked before comparative outcomes on confirmation seeds',
    development_seeds=[991300,991301],development_scope='two noncomparative endpoint-cost profiles; fully retained; not confirmation',
    seed_root=202610209101,bootstrap_seed=202610209199,families=['er','ws','sparse_sbm','pa_triadic'],graphs_per_family=8,histories_per_graph=3,n=100,k=4,portfolio_size=8,
    parameters={'D':2.,'H':10.,'trust':.9,'lambda':.2,'u':3.},rate_normalization='unchanged simulator defaults: beta1=1.15/(mean_degree*.9), beta2=3/(mean_face_incidence*.9)',
    prehistory='10% R, 10% C at random without replacement; uncontrolled 2 time units; one unconditioned attempt, retain extinctions',
    portfolio='rumor-degree top-4 anchor; seven one-swap alternatives replace its last target by next ranked outside node, degree/id deterministic ties',
    methods=['envelope','paired','uniform','rtc'],selection={'epsilon':.1,'alpha':.05,'max_calls':16384,'batch_size':32,'screen_cap':1024,'futility_after':32,'futility_fraction':.5},
    independent_evaluation_paths=256,randomization='method order randomized per context; fresh method tapes in disjoint phase coordinates; sequential single-process timing',
    accounting='all auxiliary endpoint copies charged; max_calls common; CPU/wall include Python validation, betting, allocation, trace collection and all simulation calls; exclude compilation, file compression, graph construction and prehistory',
    primary='paired graphical race / envelope-first graph-level geometric-mean capped online wall-time ratio, averaging context log ratios within graph',
    secondary='RTC paired race / envelope-first same wall-time ratio',
    multiplicity='Bonferroni two planned cost comparisons: graph bootstrap central 97.5% intervals; 20000 resamples stratified equally across four families',
    quality_gate='A matched-certified-quality efficiency claim requires every context in both methods of that comparison certified at the common epsilon/alpha. Otherwise only capped-cost and unresolved rates, not matched-quality superiority, are claimed.',
    effect_gate='adjusted lower bound > 1 for primary plus quality_gate; family directions fully reported, not a required post-hoc subset',
    descriptive=['uniform / envelope cost','marginal-continuation ratios','CPU time','envelope certification/futility frequencies','all four family strata','all 96 contexts including extinct histories','independent finite-portfolio plug-in regret with its evaluation uncertainty; no claim to known global optimum'],
    bootstrap_resamples=20000,stopping='all 32 graphs and 96 histories; no result-dependent graph, parameter, endpoint, tolerance or budget changes',
    power='32 independent graphs: approximate 80% power for mean log-cost ratio 0.58*SD at two-sided alpha=.025; developmental profiles do not estimate comparative graph-level variance, so no invented effect-based sample-size claim',
    source_sha256={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files})
p.write_text(json.dumps(cfg,indent=2)+'\n');h=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.sha256').write_text(h+'  selection_locked.json\n');print(h)
