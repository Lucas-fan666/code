"""Release validation: locked sources, lineage, full retention and PDF build."""
from pathlib import Path
import collections,csv,hashlib,json,re,sys
import numpy as np
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1];HERE=ROOT/'envelope_selection'
sys.path.insert(0,str(HERE));from study import verify

def main():
    cfg=verify();checks=[]
    def check(name,value,**extra):checks.append(dict(check=name,passed=bool(value),**extra))
    check('new locked design and declared source hashes verified',True)
    old_raw=json.loads((ROOT/'results/all_raw_sha256.json').read_text())
    available={p:h for p,h in old_raw.items() if (ROOT/p).exists()}
    missing_legacy=[p for p in old_raw if not (ROOT/p).exists()]
    check('available original raw outputs retain archived hashes',all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h for p,h in available.items()),available_files=len(available),separately_archived_unavailable_files=len(missing_legacy))
    # All old runtime sources must still verify against the old lock too.
    for lock in ['runtime_locked.json','scaling_locked.json']:
        p=ROOT/'protocol'/lock;c=json.loads(p.read_text());ok=hashlib.sha256(p.read_bytes()).hexdigest()==p.with_suffix('.sha256').read_text().split()[0]
        ok=ok and all(hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h for f,h in c.get('source_sha256',{}).items())
        check('original '+lock+' and sources retained',ok)
    summary=json.loads((HERE/'results/summary.json').read_text());check('all 32 graphs and 96 contexts included',summary['graphs']==32 and summary['contexts']==96)
    check('all 384 method/context ledgers audited',summary['accounting_checks']==384)
    rows=list(csv.DictReader((HERE/'results/context_results.csv').open()));check('exactly four methods in every context',len(rows)==384 and set(x['method'] for x in rows)==set(cfg['methods']))
    check('every context respects total copy cap',all(int(x['marginal_continuations'])<=cfg['selection']['max_calls'] for x in rows))
    for m in cfg['methods']:check(m+' certification count matches ledger',sum(x['certified']=='True' for x in rows if x['method']==m)==summary['methods'][m]['certified'])
    # Preserve every old decimal occurrence in the scientific body. Abstract
    # wording changes; the old audited numbers remain in their original body.
    old=(ROOT/'checkpoints/main_before_envelope.tex').read_text().split('\\section{Introduction}',1)[1]
    new=(ROOT/'manuscript/main.tex').read_text().split('\\section{Introduction}',1)[1]
    pattern=r'(?<![A-Za-z])\d+\.\d+'
    oc=collections.Counter(re.findall(pattern,old));nc=collections.Counter(re.findall(pattern,new))
    missing=oc-nc;check('all original body decimal values retained',not missing,missing=dict(missing))
    check('existing bibliography retained byte for byte',(ROOT/'manuscript/ref.bib').read_bytes()==(ROOT/'checkpoints/ref_before_envelope.bib').read_bytes())
    # Negative outcomes cannot disappear via a rewrite of scope statements.
    for text in ['The strict joint criterion is not met','The remaining five pool intervals contain zero','No source has a strictly positive adjusted lower bound','All twelve diagnostic pool/budget cells have negative mean gains']:
        check('retained outcome: '+text,text in new)
    check('abstract at most 300 words',len(re.search(r'\\begin\{abstract\}(.*?)\\end\{abstract\}',(ROOT/'manuscript/main.tex').read_text(),re.S).group(1).split())<=300)
    for name in ['main','supplement']:
        log=(ROOT/'manuscript'/f'{name}.log').read_text(errors='replace');check(name+' clean compilation',not any(s in log for s in ['! LaTeX Error','Overfull \\hbox','Overfull \\vbox','There were undefined references','Citation `']))
        pdf=PdfReader(ROOT/'manuscript'/f'{name}.pdf');check(name+' PDF readable',len(pdf.pages)>0,pages=len(pdf.pages))
    check('new vector figure embedded',(ROOT/'manuscript/figures/envelope_selection.pdf').read_bytes()==(HERE/'figures/envelope_selection.pdf').read_bytes())
    tests=(HERE/'results/unit_tests.txt').read_text();check('eight new tests passed','Ran 8 tests' in tests and '\nOK' in tests)
    inherited=(HERE/'results/inherited_tests.txt').read_text();check('eight inherited simulator tests passed','Ran 8 tests' in inherited and '\nOK' in inherited)
    check('new lineage exists',len(list(csv.DictReader((HERE/'results/number_lineage.csv').open())))>=15)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((HERE/'results/raw').rglob('*')) if p.is_file()}
    (HERE/'results/raw_sha256.json').write_text(json.dumps(hashes,indent=2)+'\n')
    result=dict(all_checks_pass=all(x['passed'] for x in checks) and not missing_legacy,checks=checks,limitations=[] if not missing_legacy else [f'{len(missing_legacy)} earlier runtime/scaling files unavailable'],scope='Archived-runtime hash verification, complete new-study accounting and manuscript integrity checks; not independent peer review or an acceptance prediction.')
    (HERE/'results/validation.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert result['all_checks_pass']
if __name__=='__main__':main()
