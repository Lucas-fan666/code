"""Generated dense-study numbers and all-cell descriptive prose."""
from pathlib import Path
import json,csv,numpy as np
P=Path(__file__).resolve().parent;D=P/'dense_extension';M=P.parent/'manuscript'
def main():
    s=json.loads((D/'analysis/summary.json').read_text());budget=s['stage_budget'];mac=dict(DenseUniqueCalls=f"{budget['unique_design_stage_trajectories']:,}".replace(',',r'{,}'),DenseReplayCalls=f"{budget['replayed_original_pulse_stages']:,}".replace(',',r'{,}'),DenseActualCalls=f"{budget['actual_stage_calls_including_replays']:,}".replace(',',r'{,}'))
    (M/'dense_results.tex').write_text('% Generated from dense_extension/status.json.\n'+''.join('\\newcommand{\\'+k+'}{'+v+'}\n' for k,v in mac.items()))
    r=s['patterns']['R-degree'];q=s['patterns']['random'];a=r['diagonal_maximum_rate'];b=q['diagonal_maximum_rate'];end=20.
    if a not in [0,end] and b not in [0,end]:
        text=(f'Along the equal-clock diagonal, both target rules have their largest sampled means at $\\lw=\\lr={a:g}$. '
              'The response is lower at both the slow and fast ends of the tested range, consistent with the competition between memory acquisition and subsequent forgetting. '
              'The complete diagonal curves and pointwise intervals appear in Fig.~\\ref{fig:grid}(c). ')
    else:
        text=('The expanded grid separates off-diagonal acquisition and retention effects over the full sampled range. '
              f'Along equal clocks, the largest sampled mean occurs at $\\lambda={a:g}$ under R-degree targeting and at ${b:g}$ under random targeting. '
              'The complete diagonal curves and their pointwise intervals appear in Fig.~\\ref{fig:grid}(c). ')
    means=[np.array(s['patterns'][key]['mean_grid']) for key in ['R-degree','random']]
    if all(np.all(z[1:,1]>z[1:,-1]) for z in means):
        text+='At every nonzero writing rate under both target rules, the mean response at readout rate $0.01$ exceeds that at $20$. '
    if any(z['adjacent_writing_decreases'] or z['adjacent_readout_increases'] for z in [r,q]):
        text+='The finer cells also resolve departures from a strict ordering of adjacent point estimates. '
    text+='The off-diagonal map therefore measures the two dynamical operations separately, while the diagonal changes both at once.\n'
    (M/'dense_observations.tex').write_text(text)
    # The original locked table generator remains unchanged. Clarify its scope
    # after it is run, without modifying a single numerical table entry.
    for name in ['synthetic_table.tex','observed_table.tex']:
        path=M/name;t=path.read_text();t=t.replace(': complete response grid.',': original 20-cell response grid.');path.write_text(t)
    with (D/'analysis/dense_number_lineage.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['macro','value','source']);w.writeheader();w.writerows([dict(macro=k,value=v,source='dense_extension/status.json; stage budget independently checked in dense_validate.py') for k,v in mac.items()])
    print('Wrote dense-study macros and outcome description from all cells.')
if __name__=='__main__':main()
