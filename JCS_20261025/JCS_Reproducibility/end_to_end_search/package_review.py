from pathlib import Path
import zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    files=[]
    for folder in ['protocol','reports','figures','output/pdf']:
        files.extend(p for p in (HERE/folder).rglob('*') if p.is_file())
    for name in ['summary.json','validation.json','number_lineage.json','mechanism_summary.json','continuation_ledger.json','context_costs.csv','graph_costs.csv','independent_losses.csv','archive_smoke_test.json','visual_qa.json']:
        p=HERE/'results'/name
        if p.exists():files.append(p)
    out=ROOT/'packages/JCS_Complete_Search_Review.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in files:z.write(p,str(p.relative_to(HERE)))
        z.writestr('README.txt','Completed whole-search study report, vector figures, lock, all aggregate costs and proposed LaTeX insertion. This is an experiment addendum, not a replacement journal manuscript. Complete raw trajectories and reproduction sources are in JCS_EndToEnd_Search_Complete.zip.\n')
    print(dict(path=str(out),bytes=out.stat().st_size))
if __name__=='__main__':main()
