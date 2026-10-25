"""Deterministic illustration of published confidence constants, not data."""
import math,json
from pathlib import Path
rows=[]
for M in [8,16,32]:
 n=32
 while 9*math.log(2*M*M*n*(n+1)/.05)/(n-1)>.1/10:n+=32
 threshold=math.log(2*(M-1)/.05)
 fractions=[1/32,1/16,1/8,1/4,1/2,.99];b=32
 def log_e(count):
  q=[count*math.log1p(f*.1/9.9) for f in fractions];mx=max(q)
  return mx+math.log(sum(math.exp(v-mx) for v in q)/len(q))
 while log_e(b)<threshold:b+=32
 rows.append(dict(M=M,identical_paths_eb_tapes=n,eb_copies=n*M,identical_paths_betting_tapes=b,betting_copies=b*M))
out=dict(scope='deterministic identical-path illustration; not natural-network data or another confirmatory endpoint; explains confidence-constant effects, not a new theorem',rows=rows)
p=Path(__file__).resolve().parents[1]/'results/constant_sensitivity.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
