from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'adaptive_screening'
c=json.loads((ROOT/'witness_selection/protocol/witness_locked.json').read_text())
c.update(study='Prospective independent-pilot conditional-risk screening vs frozen witness plain race',locked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),seed_root=202610219427,bootstrap_seed=202610219431,methods=['adaptive_screen','plain'],status='locked before all comparative simulation on this new cohort',routing=dict(pilot_size=4,screen_risk_fraction=.1))
c['primary']=['plain/adaptive_screen: conditional pilot-routed screen versus frozen strong unscreened witness race']
c.pop('secondary',None)
c['multiplicity']='One planned wall-time contrast; retain the previous conservative central 97.5% graph-family-stratified bootstrap interval, 20000 resamples. No secondary superiority claim. CPU/copies/families and total elapsed time are descriptive.'
c['quality_gate']='Every query in both cells certified at epsilon=.1, per-query alpha=.05, common 32768-copy cap; adjusted wall-cost ratio lower bound >1. All 96 contexts retained, including common exact extinction presolve. No conditioning on certificate success.'
c['stopping']='Exactly 32 new graphs x 3 natural histories; one new frozen policy and no outcome-driven reruns or changes. Every graph, history and unfavorable outcome is reported.'
c['budget_scope']='Same common cap 32768 as the preceding witness-refinement cohort; no further budget increase. Pilot, endpoint and candidate copies all charged. Report <=16384 prefix counts descriptively.'
c['descriptive']=['All graph families','graph sign counts','mean and total elapsed time','common exact extinction count','pilot activation and endpoint certification counts','nonpresolved results, descriptive only','copy and CPU ratios; shared zero-copy presolves contribute a neutral log-copy ratio of zero']
c['power']='32 fixed independent graphs, 8/family. With central 97.5% interval, approximate 80% detectable standardized graph log-cost effect .545. No power claim for rare erroneous certificates or equivalence.'
c['attribution_scope']='Pilot choices informed by previous development cohorts; no claim these are optimal. Gating four independent endpoint tapes at sample mean <epsilon/2; if skipped full alpha for race, if enabled alpha*.1 for screen and alpha*.9 for fresh fallback. Pilot never contributes to confirmation. The plain comparator is the frozen previous witness_plain implementation, not a weakened baseline.'
c['randomization']='Method order randomized within context; sequential timing; race seed stream shared across methods for variance reduction, separate phase coordinates for pilot and confirmations. Each method executes and pays for all its own paths; no caching across methods. Phase-local round IDs keep unmodified-race tapes aligned.'
c['preprocessing']='Both cells use identical exact rumor-extinction presolve (no R initially implies zero future rumor). Its measured wrapper cost is included. All extinctions are retained, never discarded; zero continuation count is an exact result.'
c['accounting']='Online wall and CPU include common presolve, routing, pilots, tests, simulation, validation and trace collection; exclude graph generation, prehistory, compilation and compression. Pilot four tapes = eight marginal copies. Independent evaluation remains 256 paths/action on every context.'
c['sequence_scope']='This interval concerns this new policy and cohort only, not simultaneous protection across the entire prior research sequence. Previous unsuccessful screening contrasts remain reported.'
files=[p for p in c['source_sha256'] if p.startswith(('src/','vendor/'))]+['witness_selection/selection.py','adaptive_screening/selection.py','adaptive_screening/policy.py','adaptive_screening/study.py','adaptive_screening/analyze.py','adaptive_screening/validate.py','adaptive_screening/tests/test_routing.py','adaptive_screening/theory/conditional_routing.md']
c['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
p=HERE/'protocol/adaptive_locked.json'
if p.exists():raise RuntimeError('Never overwrite a frozen protocol')
p.write_text(json.dumps(c,indent=2)+'\n');h=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.sha256').write_text(h+'  adaptive_locked.json\n');print(h)
