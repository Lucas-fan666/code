from pathlib import Path
import csv,json,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[1];legacy=ROOT/'review_inputs' if (ROOT/'review_inputs').exists() else ROOT/'legacy/04_Software_Evidence_Lite';data=legacy/'retained_results'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source={}
for rel in ['WP0/coupling_ratios_recomputed.csv','WP2/graph_policy_losses_recomputed.csv','WP2/summary.json','WP3/variance_efficiency_summary.csv']:
 source[rel]=sha(data/rel)
p=legacy/'code_configs/WP2/wp2_locked_config.json';lock_matches=sha(p)==p.with_suffix('.sha256').read_text().split()[0];assert lock_matches
summary=json.loads((data/'WP2/summary.json').read_text());assert summary['protocol_sha256']==sha(p)
eligible=summary['eligible_cells'];assert eligible==[0,2,4,5,7]
rows=list(csv.DictReader((data/'WP2/graph_policy_losses_recomputed.csv').open()));graphs=[]
for gid in sorted(set(int(r['graph']) for r in rows)):
 cellrows=[r for r in rows if int(r['graph'])==gid and int(r['cell']) in eligible];assert len(cellrows)==len(eligible)
 families={r['family'] for r in cellrows};assert len(families)==1
 graphs.append(dict(graph=gid,family=families.pop(),gain=float(np.mean([float(r['node_exchange'])-float(r['face_exchange']) for r in cellrows]))))
assert len(graphs)==60
v=np.array([g['gain'] for g in graphs]);ordered=np.sort(v);tail=int(.1*len(v));without_pa=np.array([g['gain'] for g in graphs if g['family']!='pa_triadic']);top=np.argsort(v)[-5:][::-1]
robust=dict(scope='Post hoc descriptive; not part of any locked comparison family',eligible_cells=eligible,graphs=60,mean=float(v.mean()),median=float(np.median(v)),trim_fraction_each_tail=.1,trim_count_each_tail=tail,trimmed_mean=float(ordered[tail:-tail].mean()),positive=int(sum(v>0)),negative=int(sum(v<0)),ties=int(sum(v==0)),without_pa_graphs=len(without_pa),without_pa_mean=float(without_pa.mean()),top5_share_of_net_gain=float(v[top].sum()/v.sum()),top5_graph_ids=[graphs[i]['graph'] for i in top],family_means={f:float(np.mean([g['gain'] for g in graphs if g['family']==f])) for f in sorted(set(g['family'] for g in graphs))})
wp0=list(csv.DictReader((data/'WP0/coupling_ratios_recomputed.csv').open()));initial={}
for e in ['rtc','graphical']:
 a=np.array([float(r['variance_ratio']) for r in wp0 if r['engine']==e and r['contrast']=='pair']);initial[e]=dict(comparisons=len(a),median_thinning_to_engine_variance=float(np.median(a)))
wp3=list(csv.DictReader((data/'WP3/variance_efficiency_summary.csv').open()));comparison={r['kind']:{k:float(r[k]) if k.startswith('median_') or k=='ratio_of_mean_variances' else int(r[k]) for k in ['comparisons','both_zero','graphical_zero_baseline_positive','baseline_zero_graphical_positive','finite_positive_comparisons','median_variance_ratio','ratio_of_mean_variances']} for r in wp3 if r['baseline']=='rtc'}
snapshot=ROOT/'review_inputs/main_before_review.tex'
main_path=snapshot if snapshot.exists() else ROOT/'manuscript/main.tex' if (ROOT/'manuscript/main.tex').exists() else ROOT/'inputs/main.tex';text=main_path.read_text();fragment1='The ordered-envelope theorem extends quantitative comparison to nonnested actions';fragment2='The runtime study measures computational changes'
out=dict(input_main_sha256=sha(main_path),source_sha256=source,wp2_protocol_sha256=sha(p),wp2_lock_matches=lock_matches,wp0_initial_pair=initial,wp3_rtc_over_graphical=comparison,wp2_robustness=robust,editorial_checks={'repeated_conclusion_sentence_1':text.count(fragment1),'repeated_conclusion_sentence_2':text.count(fragment2),'plural_AI_statement':text.count('They are not listed as authors.')},limits='These are recomputations from retained derived CSVs, not new stochastic simulations or an independent rerun of raw propagation labels.')
(ROOT/'results/recomputed_review_metrics.json').write_text(json.dumps(out,indent=2)+'\n')
with (ROOT/'results/wp2_graph_gain_descriptive.csv').open('w') as f:
 writer=csv.DictWriter(f,fieldnames=['graph','family','gain']);writer.writeheader();writer.writerows(graphs)
print(json.dumps(out,indent=2))
