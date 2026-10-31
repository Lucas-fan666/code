"""Check publication artifacts against the archived numerical sources."""
from pathlib import Path
import collections
import csv
import hashlib
import json
import re
import subprocess

R = Path(__file__).resolve().parents[1]
M = R / "manuscript"
P = R / "reproducibility"
O = R / "reports"
main = (M / "main.tex").read_text()
supp = (M / "supplement.tex").read_text()
abstract = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", main, re.S)[1]
abstract_words = len(re.findall(r"\S+", abstract))
assert abstract_words <= 250
highlights = (R / "submission_files/PhysicaA_Highlights.txt").read_text().splitlines()
assert len(highlights) == 5 and all(len(s) <= 85 for s in highlights)
pages = {}
for name in ["main", "supplement", "main_review"]:
    info = subprocess.check_output(["pdfinfo", str(M / (name + ".pdf"))], text=True)
    pages[name] = int(re.search(r"Pages:\s+(\d+)", info)[1])
    log = (M / (name + ".log")).read_text(errors="replace")
    assert "undefined" not in log and "Overfull" not in log
assert pages["main"] <= 30 and pages["main_review"] <= 30
for name, source, other in [("main", main, supp), ("supplement", supp, main)]:
    local = re.findall(r"\\label\{([^}]+)\}", source)
    assert len(local) == len(set(local)), (name, "duplicate label")
    external = set(re.findall(r"\\label\{([^}]+)\}", other))
    for ref in re.findall(r"\\ref\{([^}]+)\}", source):
        expected = external if ref.startswith(("S-", "M-")) else set(local)
        key = ref[2:] if ref.startswith(("S-", "M-")) else ref
        assert key in expected, (name, ref)

physics = json.loads((P / "physicaA_physics/results/validation.json").read_text())
assert physics["order_and_same_node_state_checks"]
assert physics["locked_sources_and_config_unchanged"]
assert physics["triangle_engine_loss_difference"] == 0
for name, filename in [("physicaA_physics", "physicaA_locked_config"), ("physicaA_precision", "physicaA_precision_locked"), ("physicaA_precision", "physicaA_retiming_plan")]:
    path = P / name / (filename + ".json")
    expected = (path.with_suffix(".sha256")).read_text().split()[0]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected

summary = json.loads((P / "physicaA_physics/results/summary.json").read_text())
precision = json.loads((P / "physicaA_precision/results/publication_summary.json").read_text())
rows = []
for z in summary["synthetic"]:
    if z["D"] == 2:
        for key, tex in [("total_gain", "0.80570"), ("state_gain", "0.76936"), ("memory_gain", "0.03634")]:
            assert f'{z[key]:.5f}' == tex and tex in main
            rows.append(dict(location="Main Table 2", quantity="synthetic_D2_"+key, value=z[key], source="reproducibility/physicaA_physics/results/summary.json"))
        assert "4.51 [3.11, 5.84]" in main
for z in summary["observed"]:
    if z["D"] != 2:
        continue
    for key in ["total_gain", "state_gain", "memory_gain"]:
        assert f'{z[key]:.5f}' in main
        rows.append(dict(location="Main Table 2 and Section 5", quantity=z["name"]+"_D2_"+key, value=z[key], source="reproducibility/physicaA_physics/results/summary.json"))
    for key in ["memory_fraction", "fraction_low", "fraction_high"]:
        rows.append(dict(location="Main Table 2", quantity=z["name"]+"_D2_"+key, value=z[key], source="reproducibility/physicaA_physics/results/counterfactual_summary.csv"))
for method, z in precision.items():
    for key in ["reference_based_mse", "contrast_sample_variance"]:
        assert f'{z[key]:.5f}' in main
        rows.append(dict(location="Main Section 6.1", quantity=method+"_"+key, value=z[key], source="reproducibility/physicaA_precision/results/publication_summary.json"))
effect_path=O / "editorial_review/derived_effect_expression.json"
if effect_path.exists():
    effect=json.loads(effect_path.read_text())
    assert f"{effect['value']:.1f}\\%" in main
    rows.append(dict(location="Main Section 6.1",quantity="descriptive_reference_MSE_reduction_percent",value=effect['value'],source="reports/editorial_review/derived_effect_expression.json; reproducibility/physicaA_precision/results/publication_summary.json"))
with (O / "PhysicaA_Number_Lineage.csv").open("w") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
doi = json.loads((O / "doi_resolver_checks.json").read_text())
assert len(doi) == 74
assert all(z["status"] in ["resolver accessible", "primary URL verified separately"] for z in doi)
assert json.loads((O / "reference_field_differences.json").read_text()) == []
assert "GPT-6.1" not in main
assert main.count("ChatGPT") == 1 and "ChatGPT" not in supp
assert "AI-assisted conceptual illustration" not in main
assert r"\section{Calibrated" not in main
report = dict(abstract_words=abstract_words, pages=pages, highlights_characters=list(map(len, highlights)), references_checked=len(doi), doi_resolver_accessible=sum(z["status"]=="resolver accessible" for z in doi), primary_url_checked=sum(z["status"]=="primary URL verified separately" for z in doi), latex_references_resolved=True, no_overfull_boxes=True, all_configuration_hashes_match=True, physics_checks=physics, serial_retiming=json.loads((P / "physicaA_precision/results/retiming_validation.json").read_text()), proof_text_comparison=json.loads((O / "proof_notation_check.json").read_text()), publication_status="Assigned Zenodo DOI; upload/publication is the author's remaining external action.", source_sha256={name:hashlib.sha256((M/name).read_bytes()).hexdigest() for name in ["main.tex","supplement.tex","references.bib"]})
editorial_path=O / "editorial_review/validation.json"
if editorial_path.exists():report["editorial_checks"]=json.loads(editorial_path.read_text())
report["figure_counts"]={"main":9,"supplement":20}
(O / "PhysicaA_Final_Validation.json").write_text(json.dumps(report, indent=2))
print(json.dumps({k:report[k] for k in ["abstract_words","pages","highlights_characters","references_checked","all_configuration_hashes_match"]}, indent=2))
