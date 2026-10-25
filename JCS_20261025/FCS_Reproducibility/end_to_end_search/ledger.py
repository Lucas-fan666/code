"""Separate online, independent-evaluation and repeated diagnostic work."""
from pathlib import Path
import json
import numpy as np
HERE=Path(__file__).resolve().parent
def main():
    s=json.loads((HERE/'results/summary.json').read_text());c=json.loads((HERE/'protocol/search_locked.json').read_text())
    development=sum(json.loads(p.read_text())['marginal_continuations'] for p in (HERE/'results/development').glob('graph_*/history_*/*.json') if p.name in [m+'.json' for m in c['methods']])
    profile=0;grid=0
    for p in (HERE/'results/mechanisms').glob('graph_*/records.json'):
        for q in json.loads(p.read_text()):
            if 'M' in q:grid+=q['copies']
            else:profile+=q['copies']
    ledger=dict(confirmation_online=s['online_marginal_continuations'],independent_final_evaluation=s['independent_evaluation_continuations'],
        development_online=development,diagnostic_search_workloads=dict(profiled=profile,frozen_engine_reference=profile),
        diagnostic_fixed_portfolios=dict(frozen_engine=grid,profiled_reference=grid),
        propagation_total_excluding_prehistory_and_unit_tests=s['online_marginal_continuations']+s['independent_evaluation_continuations']+development+2*profile+2*grid,
        prehistory_runs=dict(confirmation=c['graphs']*c['histories_per_graph'],development=8,mechanism_reconstruction=8),
        decision_reconstruction_new_propagation=0,
        unit_tests=dict(marginal_continuations_per_full_new_test_suite=1934,scope='Small fixed synthetic validation cases; outside confirmation. Two suites ran before the lock; fresh archive verification runs another suite. Additional user reruns are not part of the original study ledger.'),
        conventions=['All native calls charge actions times tapes, including zero-event losses and repeated diagnostic references.',
                     'Diagnostic fixed workloads are repeated computations, not independent graphs or extra efficacy samples.',
                     'Prehistory trajectories have a different duration and are listed separately.',
                     'Only confirmation_online enters the whole-search selection budget; final evaluation and diagnostics are excluded from its timing.'])
    assert profile==8*3*c['search']['online_budget']
    assert grid==8*sum(c['mechanisms']['portfolio_sizes'])*len(c['mechanisms']['overlaps'])*c['mechanisms']['tapes']*3
    (HERE/'results/continuation_ledger.json').write_text(json.dumps(ledger,indent=2)+'\n');print(ledger)
if __name__=='__main__':main()
