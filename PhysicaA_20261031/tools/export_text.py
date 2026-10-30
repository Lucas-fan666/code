"""Export the complete main text to readable Markdown and plain text."""
from pathlib import Path
import re
import subprocess
import tempfile

R = Path(__file__).resolve().parents[1]
M = R / "manuscript"
O = R / "submission_files"
O.mkdir(exist_ok=True)
s = (M / "main.tex").read_text()
labels = {}
for name, prefix in [("main", ""), ("supplement", "S-")]:
    aux = (M / (name + ".aux")).read_text()
    labels.update({prefix + a: b for a, b in re.findall(r"\\newlabel\{([^}]+)\}\{\{([^}]+)\}", aux)})
citations = dict(re.findall(r"\\bibcite\{([^}]+)\}\{\{?(\d+)", (M / "main.aux").read_text()))

title = re.search(r"\\title\{([^}]+)\}", s)[1]
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", s, re.S)[1]
keywords = re.search(r"\\begin\{keyword\}(.*?)\\end\{keyword\}", s, re.S)[1].replace(r"\sep", ";")
s = s.split(r"\section{Introduction}", 1)[1]
s = r"\section{Introduction}" + s
s = s.split(r"\begingroup", 1)[0]
s = re.sub(r"(?m)^%.*$", "", s)
s = re.sub(r"\\cite\{([^}]+)\}", lambda m: "[" + ", ".join(citations[k] for k in m[1].split(",")) + "]", s)
s = re.sub(r"\\ref\{([^}]+)\}", lambda m: labels[m[1]], s)
s = re.sub(r"\\label\{[^}]+\}", "", s)
counter = [0]
def theorem(m):
    counter[0] += 1
    label = m[1].capitalize() + " " + str(counter[0])
    if m[2]:
        label += " (" + m[2] + ")"
    return r"\subsection*{" + label + "}"
s = re.sub(r"\\begin\{(theorem|proposition|corollary|lemma)\}(?:\[([^\]]+)\])?", theorem, s)
s = re.sub(r"\\end\{(?:theorem|proposition|corollary|lemma)\}", "", s)
s = s.replace(r"\begin{proof}", r"\paragraph{Proof.}").replace(r"\end{proof}", r"\(\square\)")
# Remove only the sizing wrapper, preserving the full table contents.
s = re.sub(r"\\resizebox\{\\(?:textwidth|linewidth)\}\{!\}\{(?=\\begin\{tabular\})", "", s).replace(r"\end{tabular}}", r"\end{tabular}")
for cmd, value in [(r"\E", r"\mathbb{E}"), (r"\Prob", r"\mathbb{P}"), (r"\Fset", r"\mathcal{F}"), (r"\Var", r"\operatorname{Var}"), (r"\ind", r"\mathbf{1}"), (r"\Gain", r"\mathcal{G}")]:
    s = re.sub(re.escape(cmd) + r"(?![A-Za-z])", lambda m: value, s)
s = s.replace(r"\FloatBarrier", "").replace(r"\centering", "")
bbl = (M / "main.bbl").read_text()
entries = re.split(r"\\bibitem\{([^}]+)\}", bbl)[1:]
refs = []
for i in range(0, len(entries), 2):
    key, body = entries[i:i+2]
    body = body.split(r"\end{thebibliography}")[0].replace(r"\newblock", " ")
    refs.append(r"\par\noindent [" + citations[key] + "] " + body)
s = (r"\section*{" + title + "}\nJunkai Fan\n\nSchool of Business Administration, Northeastern University, Shenyang 110169, China\n\nfanjk@mails.neu.edu.cn\n\n" + r"\section*{Abstract}" + abstract + "\n\n" + r"\paragraph{Keywords.}" + keywords + "\n\n" + s + r"\section*{References}" + "\n".join(refs))
with tempfile.TemporaryDirectory(prefix="physicaA_text_") as td:
    tex = Path(td) / "text.tex"
    tex.write_text(s)
    (R / "reports/readable_export_input.tex").write_text(s)
    subprocess.run(["pandoc", str(tex), "-f", "latex", "-t", "gfm", "--wrap=none", "-o", str(O / "PhysicaA_Full_English_Manuscript.md")], check=True)
subprocess.run(["pdftotext", "-layout", str(M / "main.pdf"), str(O / "PhysicaA_Full_English_Manuscript.txt")], check=True)
assert counter[0] == 8
md = (O / "PhysicaA_Full_English_Manuscript.md").read_text()
for phrase in ["Exact grand coupling", "A variance bound for nonnested actions", "Proof.", "Declaration of competing interest", "References"]:
    assert phrase in md, phrase
print("Exported the complete main text, eight numbered results, proofs and references.")
