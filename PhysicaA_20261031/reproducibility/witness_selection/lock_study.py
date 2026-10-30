from pathlib import Path
import datetime,hashlib,json
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'witness_selection'
c=json.loads((ROOT/'coupling_factorial/protocol/factorial_locked.json').read_text())
c.update(study='Prospective fixed-witness certification refinement',locked_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),seed_root=202610217813,bootstrap_seed=202610217819,methods=['old_screen','witness_screen','witness_plain'],status='locked before any comparative simulation on this cohort')
c['selection']['max_calls']=32768
c['primary']=['old_screen/witness_screen: same screen and engine; original all-pairs bound versus proved fixed-witness bound']
c['secondary']=['witness_plain/witness_screen: endpoint-screen policy effect with the same improved bound']
c['multiplicity']='Both planned wall-time contrasts jointly protected by Bonferroni: family-stratified graph-unit bootstrap 20,000 draws, central 97.5% intervals. No unadjusted superiority claims from CPU, copies or family summaries.'
c['quality_gate']='All 96 queries in both compared cells must be certified at common epsilon=.1 and alpha=.05; wall-time ratio adjusted lower bound >1. No conditioning on certified contexts. Failed gates remain reported.'
c['stopping']='Exactly 32 new graphs x 3 histories; all outcomes retained; no reruns to improve gate outcomes; no change to grids, methods, epsilon, alpha or budget after results.'
c['budget_scope']='Common cap 32768 charged marginal copies, twice earlier cap. Report certified-by-16384 count separately as a descriptive prefix. Mechanism attribution compares cells under the SAME new cap. Do not attribute improved coverage over previous cohorts solely to mechanism.'
c['descriptive']=['Certified-by-16384 prefix counts','arithmetical mean wall time and total wall time','all graph families and graph sign counts','charged copies and CPU','independent evaluation means, not false-certificate-rate estimates']
c['power']='32 fixed independent graphs, 8/family. Approximate 80% detectable standardized log-cost effect (2.241+0.842)/sqrt(32)=0.545 for a two-sided .025 contrast; cannot establish rare-error rates or equivalence.'
c['attribution_scope']='Only pairwise race threshold is refined. Engine, mixture bets, batches, root-screen alpha/2 allocation and futility remain frozen. witness_screen threshold log[4(M-1)/alpha]; witness_plain log[2(M-1)/alpha]. Fresh independent method streams; randomized sequential order.'
c.pop('preprocessing',None)
files=[p for p in c['source_sha256'] if p.startswith(('src/','vendor/'))]+['coupling_factorial/selection.py','witness_selection/selection.py','witness_selection/study.py','witness_selection/analyze.py','witness_selection/validate.py','witness_selection/tests/test_witness.py','witness_selection/theory/witness_bound.md']
c['source_sha256']={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}
p=HERE/'protocol/witness_locked.json'
if p.exists():raise RuntimeError('Never overwrite a locked protocol')
p.write_text(json.dumps(c,indent=2)+'\n');h=hashlib.sha256(p.read_bytes()).hexdigest();p.with_suffix('.sha256').write_text(h+'  witness_locked.json\n');print(h)
