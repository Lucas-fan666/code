"""Fetch public release inputs after the reserved Zenodo record is published."""
from pathlib import Path
from zipfile import ZipFile
import urllib.request,urllib.error,json,hashlib
R=Path(__file__).resolve().parent;record='https://zenodo.org/api/records/23811459'
try:
 with urllib.request.urlopen(record,timeout=30) as f:data=json.load(f)
except urllib.error.HTTPError as e:
 if e.code==404:raise SystemExit('The assigned record is not public yet. Upload and publish the release before using this downloader.')
 raise
needed=['PhysicaA_Physical_Response_Data.zip','PhysicaA_LaTeX_Source.zip']
for key in needed:
 items=[v for v in data['files'] if v['key']==key]
 if len(items)!=1:raise SystemExit('Expected archive is not present in the public record: '+key)
 item=items[0];path=R/key
 with urllib.request.urlopen(item['links']['self'],timeout=90) as f,path.open('wb') as out:
  while True:
   b=f.read(1024*1024)
   if not b:break
   out.write(b)
 assert 'md5:'+hashlib.md5(path.read_bytes()).hexdigest()==item['checksum']
 with ZipFile(path) as z:
  target=R.parent if key.endswith('Data.zip') else R/'manuscript'
  for member in z.namelist():
   resolved=(target/member).resolve()
   if not resolved.is_relative_to(target.resolve()):raise ValueError('Unsafe archive path')
  z.extractall(target)
print('Inputs retrieved and checksums verified. Run python run_physicaA.py.')
