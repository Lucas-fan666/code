from pathlib import Path
import hashlib,json,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
def main():
    c=json.loads((HERE/'protocol/search_locked.json').read_text())
    files={ROOT/name for name in c['source_sha256']}
    files.update(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'pdf_qa' not in p.parts and 'build' not in p.parts and p.suffix not in ['.pyc','.so'])
    # Only include atomically finished contexts when saving a running checkpoint.
    raw=HERE/'results/raw'
    for p in list(files):
        if raw in p.parents and not (p.parent/'complete.json').exists():files.remove(p)
    wrapper=ROOT/'reproduce_end_to_end_search.py'
    if wrapper.exists():files.add(wrapper)
    out=ROOT/'packages/FCS_EndToEnd_Search_Complete.zip'
    with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        z.writestr('end_to_end_search/build/',b'')
        for p in sorted(files):z.write(p,str(p.relative_to(ROOT)))
        if (HERE/'README.md').exists():z.writestr('README.md',(HERE/'README.md').read_text())
    print(json.dumps(dict(path=str(out),bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),files=len(files)),indent=2))
if __name__=='__main__':main()
