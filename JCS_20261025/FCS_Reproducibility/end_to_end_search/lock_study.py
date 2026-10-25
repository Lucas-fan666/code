from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=HERE/'protocol/search_locked.json'
    if p.exists():raise RuntimeError('A lock already exists; never overwrite a completed or running design')
    dev=json.loads((HERE/'results/development/planning_summary.json').read_text());assert dev['all_replay_batch_exact']
    files=[*list((HERE).glob('*.py')),*list((HERE/'tests').glob('*.py')),*list((ROOT/'src').glob('*.py')),*list((ROOT/'src').glob('*.cpp')),*list((ROOT/'vendor/src').glob('*.py')),*list((ROOT/'vendor/src').glob('*.cpp'))]
    c=dict(study='Complete adaptive greedy-plus-FEX search at preserved graphical joint law',locked_at_utc=datetime.now(timezone.utc).isoformat(),status='Locked before confirmation graph generation, comparative costs or outcomes',
        seed_root=202610218301,bootstrap_seed=202610218399,development_seed_root=202610218201,
        graphs=dev['graphs_planned'],histories_per_graph=3,families=['er','ws','sparse_sbm','pa_triadic'],sizes=[100,300],graphs_per_family_size=dev['graphs_planned']//8,
        methods=['graphical','fixed_batch','adaptive_local','local_rtc'],parameters={'D':2.,'H':10.},
        search=dict(k=4,candidate_pool=16,anchor_budget=512,online_budget=1024),evaluation_paths=256,
        prehistory='Exactly10% R,10% C,80% U; zero memory; two uncontrolled time units; one unconditioned attempt per history; all extinction cases retained; same contexts for all methods',
        selection='Existing vendor/src/set_search.py greedy + face exchange; four adaptive singleton-greedy stages, then at most13 FEX proposals; independent discovery and holdout. Only evaluation organization changes. New independent seeds per stage. No optional statistical screening or altered test thresholds.',
        allocation='Outcome-independent uniform integer counts with randomized remainder. Common prefix plus one independent tape on remainder subset; full marginal counts charged. Same allocations and stage keys in all methods.',
        primary=dict(contrast='graphical/adaptive_local whole-search wall time',aggregation='sum three context times within each graph, then mean graph log ratio',confidence=.95,gate='source/tests/replay checks pass AND primary interval lower bound>1; same graphical adaptive output law follows from theorem assumptions, not non-significance of loss comparisons'),
        secondary=dict(contrasts=['fixed_batch/adaptive_local wall time','local_rtc/adaptive_local wall time'],confidence=.975,multiplicity='Bonferroni across two secondary cost contrasts; RTC is equal-budget only, not a matched-quality claim'),
        bootstrap='Resample independent graphs within each of eight family/size strata, preserving all histories; percentile bootstrap',bootstrap_resamples=20000,
        descriptive=['CPU time','oracle vs other whole-search cost','every family/size ratio','independent final selected-action losses, no test-minimum oracle','all failures, including fixed_batch outperforming adaptive_local'],
        mechanisms=dict(graphs='First graph in each of eight family/size cells, history0',portfolio_sizes=[2,8,16,32],overlaps=['common_three','random_four_sets'],tapes=8,
            profile='Separate untimed diagnostic pass on the identical stored replay-query workloads for graphical/fixed_batch/adaptive_local; instrumented losses and counters checked against frozen engine; topology, copy initialization where available, remaining engine time; event counters. No isolated scheduling-time claim.',inference='Descriptive only; every planned cell retained'),
        timing='Sequential methods in randomized order per context; no concurrent benchmark workers. Whole-search candidate creation/ranking, validations, inference, trace collection, initialization and native calls included; reusable simulator construction/compilation, graph/prehistory, final evaluation and disk serialization excluded.',
        stopping='All planned graphs and histories; no significance stopping, no outcome-driven changes; resumable only for incomplete contexts',
        planning=dev,scope='No FEX superiority claim, no whole-objective approximation or deployment-effect claim, no loss equivalence claim for RTC; cost evidence concerns these graph sizes and candidate rule',
        source_sha256={str(f.relative_to(ROOT)):sha(f) for f in sorted(set(files))})
    p.write_text(json.dumps(c,indent=2)+'\n');p.with_suffix('.sha256').write_text(sha(p)+'  search_locked.json\n');print(dict(graphs=c['graphs'],contexts=c['graphs']*3,sha256=sha(p),expected_seconds=dev['expected_confirmation_seconds']))
if __name__=='__main__':main()
