"""Check proof text after the documented notation and reference renaming."""
from pathlib import Path
import collections
import hashlib
import json
import re

R = Path(__file__).resolve().parents[1]
def canonical(s):
    replacements = [(r'\Delta_{SW}',r'\Delta'),(r'\sigma',r'\Delta'),(r'T_{\mathrm{set}}','T'),(r'T_{0,f}','T_f'),('T_0','T'),(r'B_{\mathrm{env},r}','B_r'),(r'B_{\mathrm{env}}','B'),('B_g','B'),(r'K_{\mathrm{hor}}','K'),(r'K_{\mathrm{tot}}','K'),(r'\tau_{\mathrm{hit}}','T'),(r'\mathcal E_{\mathrm{sw}}','B'),(r'Z_{\mathrm{Ber}}','B')]
    for a,b in replacements:
        s = s.replace(a,b)
    s = re.sub(r'\\ref\{[SM]-',lambda m:r'\ref{',s)
    s = re.sub(r'_\{([A-Za-z])\}',r'_\1',s)
    return re.sub(r'\s+','',s)
def fingerprints(s):
    return [hashlib.sha256(canonical(z).encode()).hexdigest() for z in re.findall(r'\\begin\{proof\}(.*?)\\end\{proof\}',s,re.S)]
if __name__ == '__main__':
    expected = json.loads((R/'reports/PhysicaA_Proof_Fingerprints.json').read_text())['canonical_proof_sha256']
    actual = fingerprints((R/'manuscript/main.tex').read_text()) + fingerprints((R/'manuscript/supplement.tex').read_text())
    assert collections.Counter(expected) == collections.Counter(actual)
    print(f'{len(actual)} proof blocks match after the documented textual normalization; this is not independent proof certification.')
