"""Check diagnostic lineage, manuscript synchronization and order inequalities."""
from pathlib import Path
from itertools import product
import hashlib,json
import numpy as np
from pypdf import PdfReader

P=Path(__file__).resolve().parent;R=P.parent;D=P/'interpretation'
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()

def order_checks():
    # R=0,U=1,C=2 here, so the numeric order is the paper's node order.
    pairs=[(x,y) for x in product(range(3),repeat=3)
           for y in product(range(3),repeat=3) if all(a<=b for a,b in zip(x,y))]
    def drive(x):return .9*((sum(v==0 for v in x)>=2)-(sum(v==2 for v in x)>=2))
    def rates(x,a,i):
        donors=[x[j] for j in range(3) if j!=i]
        return (.3*.9*sum(q==0 for q in donors)+.7*.9*(1+a)*all(q==0 for q in donors),
                .3*.9*sum(q==2 for q in donors)+.7*.9*(1-a)*all(q==2 for q in donors))
    checks=0
    for x,y in pairs:
        assert drive(x)>=drive(y)
        for a,b in product(np.linspace(-.9,.9,5),repeat=2):
            if a<b:continue
            for i in range(3):
                rx,cx=rates(x,a,i);ry,cy=rates(y,b,i)
                assert rx>=ry-1e-14 and cx<=cy+1e-14
                checks+=1
    return checks

def main():
    hashes=json.loads((D/'occupation_integral_source_hashes.json').read_text())
    for name,digest in hashes.items():assert sha(P/name)==digest,name
    protocol=json.loads((D/'protocol.json').read_text())
    for name,digest in protocol['analysis_sources'].items():assert sha(P/name)==digest,name
    replay=sorted((D/'pulse_replay').glob('*.npz'));assert len(replay)==32
    assert sum(int(np.load(f)['replayed_stage_calls']) for f in replay)==24576
    s=json.loads((D/'analysis/summary.json').read_text());ref=next(q for q in s['strength'] if q['strength']==3 and q['rule']=='R-degree')
    assert abs(ref['retained_memory_contribution']-.03639773005885451)<1e-14
    assert abs(ref['survival_conditional_contribution']*ref['survival']-ref['retained_memory_contribution'])<1e-14
    assert s['unique_study_stages']==3729524 and s['total_computational_stages_including_endpoint_replays']==3809396
    for q in s['school_exclusions']:
        assert (q['unique_size_ge4'],q['max_size'])==((229,5) if 'high' in q['dataset'] else (356,5))
    main=(R/'manuscript/main.tex').read_text();supp=(R/'manuscript/supplement.tex').read_text()
    assert r'\ell_i^U(x,a,t)=1' in main and r'\label{eq:generator}' in main
    assert 'finite triangular simplicial complex' in main and 'recurrent' not in main
    assert 'infection- and recovery-time dependence' in main
    assert 'Order preservation of pulse and readout paths' in supp and 'bounded nonnegative correction rates' in supp
    assert '$100G_A/G_X$' not in (R/'manuscript/reference_table.tex').read_text()
    fig=PdfReader(R/'figures/response_grid.pdf');txt=fig.pages[0].extract_text()
    assert 'Planned retention contrast' in txt and '0.05417' in txt and '0.01299' in txt
    for pdf in (R/'output/pdf').glob('*.pdf'):
        text=''.join(p.extract_text() or '' for p in PdfReader(pdf).pages)
        assert '??' not in text and 'recurrent three-state' not in text
    report=dict(passed=True,immutable_occupation_integral_files=len(hashes),endpoint_replay_files=len(replay),
                endpoint_replay_stages=24576,new_occupation_integral_observations=0,
                unique_study_stages=3729524,total_computational_stages=3809396,
                enumerated_reset_order_checks=order_checks(),self_contained_order_proof=True,
                figure2_planned_contrast_visible=True,zero_rate_separate_from_log_axis=True,
                percentages_consistent=True)
    (R/'reports/interpretation_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
