"""Content, evidence and lineage checks for the CSV-backed review corrections.

This checks the revised report; it is not an independent propagation rerun.
"""
from pathlib import Path
import csv, hashlib, json, re, sys
from pypdf import PdfReader
from apply_content_revisions import revise_main

ROOT = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
text = (ROOT / 'manuscript/main.tex').read_text()
metrics = json.loads((ROOT / 'results/recomputed_review_metrics.json').read_text())
checks = []
def check(name, passed, **detail):
    checks.append(dict(check=name, passed=bool(passed), **detail))

snapshot = ROOT / 'review_inputs/main_before_review.tex'
check('audit snapshot unchanged', sha(snapshot) == metrics['input_main_sha256'])
for name, digest in metrics['source_sha256'].items():
    check('retained input: ' + name, sha(ROOT/'review_inputs/retained_results'/name) == digest)
lock = ROOT/'review_inputs/code_configs/WP2/wp2_locked_config.json'
check('WP2 locked configuration and recorded hash', sha(lock) == metrics['wp2_protocol_sha256'] == lock.with_suffix('.sha256').read_text().split()[0])
for filename in ['runtime_locked.json', 'scaling_locked.json']:
    path = ROOT/'protocol'/filename
    cfg = json.loads(path.read_text())
    check(filename + ' and source hashes unchanged', sha(path) == path.with_suffix('.sha256').read_text().split()[0] and all(sha(ROOT/p) == digest for p,digest in cfg['source_sha256'].items()))

check('correction function is idempotent on final text', revise_main(text, metrics) == text)
conclusion = text.split('\\section{Conclusion}',1)[1].split('\\section*{Acknowledgements and funding}',1)[0].strip()
sentences = re.findall(r'\.(?:\s+(?=[A-Z])|$)', conclusion)
check('conclusion: one paragraph and six sentences', '\n\n' not in conclusion and len(sentences) == 6, sentences=len(sentences))
check('original duplicated sentences removed', all(fragment not in text for fragment in ['The ordered-envelope theorem extends quantitative comparison to nonnested actions','The runtime study measures computational changes']))
check('AI authorship statement singular and synchronized', text.count('It is not listed as an author.') == 1 and 'ChatGPT is not listed as an author.' in (ROOT/'reports/cover_letter_updated.md').read_text())
check('both added runtime cohorts occur once in overview', text.count('Portfolio runtime &') == 1 and text.count('Large portfolio extension &') == 1)
check('RTC variance and robustness blocks occur once', text.count('% BEGIN REVIEW_RTC_VARIANCE') == 1 and text.count('% BEGIN REVIEW_ROBUSTNESS') == 1 and text.count('\\label{tab:robustness}') == 1)
check('descriptive scaling extension retained', text.count('\\paragraph{Larger graphs and portfolios.}') == 1)
abstract = text.split('\\begin{abstract}',1)[1].split('\\end{abstract}',1)[0]
check('abstract within 300 words', len(abstract.split()) <= 300, words=len(abstract.split()))
check('original audit retains five repetitions per sentence', metrics['editorial_checks']['repeated_conclusion_sentence_1'] == 5 and metrics['editorial_checks']['repeated_conclusion_sentence_2'] == 5)
for name in ['main','supplement']:
    log = (ROOT/'manuscript'/f'{name}.log').read_text(errors='replace')
    check(name + ' compile: no errors, unresolved references or overfull boxes', not re.search(r'Overfull|There were undefined|Citation .* undefined|Reference .* undefined|^!', log, re.M))
    check(name + ' PDF is readable', len(PdfReader(ROOT/'manuscript'/f'{name}.pdf').pages) > 0)

lineage=[]
def add(name,value,scope,source,calculation):
    lineage.append(dict(metric=name,value=value,scope=scope,input=source,input_sha256=metrics['source_sha256'][source],calculation=calculation,script='scripts/recompute_review_metrics.py'))
for engine, values in metrics['wp0_initial_pair'].items():
    add('initial_thinning_over_'+engine,values['median_thinning_to_engine_variance'],'initial nested pair; descriptive','WP0/coupling_ratios_recomputed.csv',f'median(variance_ratio | contrast=pair, engine={engine})')
for kind,values in metrics['wp3_rtc_over_graphical'].items():
    for key in ['median_variance_ratio','ratio_of_mean_variances','comparisons','finite_positive_comparisons','both_zero','graphical_zero_baseline_positive','baseline_zero_graphical_positive']:
        add('rtc_over_graphical_'+kind+'_'+key,values[key],'decision-cost cohort; descriptive','WP3/variance_efficiency_summary.csv','retained summary row: baseline=rtc, kind='+kind+', field='+key)
for key in ['mean','median','trimmed_mean','positive','negative','ties','without_pa_mean','top5_share_of_net_gain']:
    add('wp2_posthoc_'+key,metrics['wp2_robustness'][key],'post hoc descriptive; outside locked comparison family','WP2/graph_policy_losses_recomputed.csv','graph mean(node_exchange-face_exchange) over eligible cells [0,2,4,5,7]; '+key)
with (ROOT/'results/review_number_lineage.csv').open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['metric','value','scope','input','input_sha256','calculation','script']);writer.writeheader();writer.writerows(lineage)
out=dict(all_checks_pass=all(c['passed'] for c in checks),checks=checks,final_main_sha256=sha(ROOT/'manuscript/main.tex'),new_research_experiment_paths=0,scope='Content and retained-CSV recomputation checks; existing correctness tests are separate from research experiments. Old experiments are retained, no new efficacy or acceptance claim.')
(ROOT/'results/content_review_validation.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2));sys.exit(0 if out['all_checks_pass'] else 1)
