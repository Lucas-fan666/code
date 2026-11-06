from pathlib import Path
import subprocess,shutil,re,json
P=Path(__file__).resolve().parent;O=P.parent/'output/pdf';O.mkdir(parents=True,exist_ok=True)
def build(name):
 for i in range(4):
  run=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error',name+'.tex'],cwd=P,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
  (P/(name+'.stdout.txt')).write_text(run.stdout)
  if run.returncode:print(run.stdout[-6000:]);raise SystemExit(run.returncode)
  if i==0:
   bib=subprocess.run(['bibtex',name],cwd=P,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
   if bib.returncode:print(bib.stdout);raise SystemExit(bib.returncode)
 log=(P/(name+'.log')).read_text(errors='replace')
 if any(w in log for w in ['There were undefined','multiply defined','Overfull']):
  print('\n'.join(l for l in log.splitlines() if any(x in l for x in ['undefined','Overfull','multiply defined'])));raise SystemExit('Final TeX diagnostics require review: '+name)
 return log
# Synchronize presentation terminology after generated numerical tables.
for generated in ['mechanism_diagnostics.tex', 'dense_observations.tex', 'strength_diagnostics.tex', 'strength_diagnostic_table.tex']:
 path=P/generated
 if path.exists():
  text=path.read_text()
  text=text.replace('initial occupation-retention relaxation rate','initial occupation-response rate')
  text=text.replace('initial occupation-readout rate','initial occupation-response rate')
  text=text.replace('readout rate','retention relaxation rate')
  text=text.replace('$v_D$',r'$\nu_D^{\rm tr}$').replace('$10^3v_D$',r'$10^3\nu_D^{\rm tr}$')
  text=text.replace('subsequent forgetting','post-withdrawal relaxation')
  path.write_text(text)
# Current school tables use the same ten-history estimates and nested intervals as the maps.
# The original three-history arrays remain archived for provenance and sensitivity analysis.
import csv
observed_csv=P.parent/'reproducibility/reviewer_extension/analysis/observed_grid.csv'
if observed_csv.exists():
 rows=list(csv.DictReader(observed_csv.open()))
 lookup={(r['dataset'],float(r['write']),float(r['read']),r['rule'],r['observable']):r for r in rows}
 tables=[]
 for dataset,title in [('contact-high-school','High-school'),('contact-primary-school','Primary-school')]:
  lines=[r'\small\begin{longtable}{llccc}',
   r'\caption{'+title+r' topology: selected 20 rate pairs from the ten-history study. Entries have time units; intervals are pointwise $95\%$ nested history-and-replication bootstrap intervals.}\\',
   r'\toprule',r'Rule; $\lw$ & $\lr$ & $G_A$ [interval] & $G_A^{\rm rev}$ & $\overline G_A$\\\midrule\endfirsthead',
   r'\toprule Rule; $\lw$ & $\lr$ & $G_A$ [interval] & $G_A^{\rm rev}$ & $\overline G_A$\\\midrule\endhead',r'\bottomrule\endfoot']
  for rule in ['R-degree','random']:
   for w in [0,.02,.2,2]:
    for rr in [0,.02,.2,2,20]:
     f=lookup[dataset,w,rr,rule,'forward'];rev=lookup[dataset,w,rr,rule,'reverse'];avg=lookup[dataset,w,rr,rule,'order_average']
     lines.append(f"{rule}; {w:g} & {rr:g} & {float(f['mean']):.5f} [{float(f['lower']):.5f}, {float(f['upper']):.5f}] & {float(rev['mean']):.5f} & {float(avg['mean']):.5f}"+r'\\')
  lines.append(r'\end{longtable}\normalsize');tables.append('\n'.join(lines))
 (P/'observed_table.tex').write_text('\n\n'.join(tables)+'\n')

for name,target in [('main','PhysicaA_Manuscript_Write_Read'),('supplement','PhysicaA_Supplement_Write_Read')]:
 build(name);shutil.copy2(P/(name+'.pdf'),O/(target+'.pdf'))
review=(P/'main.tex').read_text().replace('[final,5p,times,twocolumn,sort&compress]','[preprint,11pt,sort&compress]').replace('{figure*}','{figure}').replace('{table*}','{table}').replace('width=17cm',r'width=\linewidth')
review=review.replace(r'\input{reference_table}',r'\resizebox{\linewidth}{!}{\input{reference_table}}')
review=review.replace(r'\input{preamble}',r'\input{preamble}'+ '\n'+r'\usepackage[a4paper,left=18mm,right=18mm,top=20mm,bottom=20mm]{geometry}'+ '\n'+r'\renewcommand{\topfraction}{.95}'+ '\n'+r'\renewcommand{\floatpagefraction}{.75}'+ '\n'+r'\setcounter{topnumber}{2}'+ '\n'+r'\journal{Physica A}')
(P/'review.tex').write_text(review);build('review');shutil.copy2(P/'review.pdf',O/'PhysicaA_Review_Write_Read.pdf')
print('Main, supplement and review copy compiled without unresolved references or overfull boxes.')
