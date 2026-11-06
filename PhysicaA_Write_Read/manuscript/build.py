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
  path.write_text(text)
for name,target in [('main','PhysicaA_Manuscript_Write_Read'),('supplement','PhysicaA_Supplement_Write_Read')]:
 build(name);shutil.copy2(P/(name+'.pdf'),O/(target+'.pdf'))
review=(P/'main.tex').read_text().replace('[final,5p,times,twocolumn,sort&compress]','[preprint,11pt,sort&compress]').replace('{figure*}','{figure}').replace('{table*}','{table}').replace('width=17cm',r'width=\linewidth')
review=review.replace(r'\input{reference_table}',r'\resizebox{\linewidth}{!}{\input{reference_table}}')
review=review.replace(r'\input{preamble}',r'\input{preamble}'+ '\n'+r'\usepackage[a4paper,left=18mm,right=18mm,top=20mm,bottom=20mm]{geometry}'+ '\n'+r'\renewcommand{\topfraction}{.95}'+ '\n'+r'\renewcommand{\floatpagefraction}{.75}'+ '\n'+r'\setcounter{topnumber}{2}'+ '\n'+r'\journal{Physica A}')
(P/'review.tex').write_text(review);build('review');shutil.copy2(P/'review.pdf',O/'PhysicaA_Review_Write_Read.pdf')
print('Main, supplement and review copy compiled without unresolved references or overfull boxes.')
