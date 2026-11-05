#!/usr/bin/env python3
"""Create a self-contained Zenodo archive from the saved code/data release.

Usage:
    python restore_zenodo_archive.py /path/to/PhysicaA_Code_Data_Write_Read.zip

Requires Python 3.9+ and NumPy.  The input ZIP is never changed.  The 64
strength-analysis input files are reconstructed from the already-archived
merged arrays; no new simulation observations are generated.
"""
from pathlib import Path, PurePosixPath
import hashlib
import io
import json
import sys
import zipfile

try:
    import numpy as np
except ImportError:
    raise SystemExit("NumPy is required. Install it with: python -m pip install numpy")

ROOT = "PhysicaA_Memory_Write_Read/"
INPUT_SHA256 = "d247bdebb1af487880ebb2357dd1f66cb24849a07af358720f681f02efca9ed2"
HASH_LIST = ROOT + "reproducibility/interpretation/occupation_integral_source_hashes.json"
REVIEW = ROOT + "reproducibility/reviewer_extension/"
TARGET_NAME = "PhysicaA_Zenodo_Code_Data_Recovered.zip"

README = """# Writing, retention and dynamical readout of group memory in higher-order spreading

This archive contains the simulation and analysis sources, fixed protocols,
saved seeds, realized topologies, all raw results, figure code and manuscript
sources for the study.

The 100-pair grid includes 34 original, 34 dense-grid and 34 robustness or
school-extension result files. The 64 strength-analysis inputs were recovered
from the loss and dose arrays in the corresponding merged result files. The
recovery checks all 102 original-result SHA-256 hashes and performs no new
simulation.

To reproduce the article from the saved data, unpack this archive, enter the
PhysicaA_Memory_Write_Read directory and run:

    python -m pip install -r requirements.txt
    python reproduce.py --from-data

The workflow also needs a C++17 compiler, Cairo, pdflatex and bibtex.
The two school datasets provide contact structures for synthetic spreading
dynamics; their source, preprocessing rule and hashes are documented under
reproducibility/inputs/. Third-party asset and font licenses accompany their
files. An archive DOI has not yet been assigned.
"""

def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()

def sha_file(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def file_parts(name):
    return PurePosixPath(name).parts

def omitted(name):
    parts = file_parts(name)
    if not parts or parts[0] != ROOT.rstrip("/") or ".." in parts:
        raise ValueError("Unexpected path in source archive: " + name)
    rel = parts[1:]
    if not rel:
        return True
    if rel[0] in ("tmp", "submission"):
        return True
    if rel[:2] == ("reports", "history"):
        return True
    if rel[:3] == ("reproducibility", "reviewer_extension", "parts"):
        return True
    if rel[0] == "output" and rel[-1] not in (
        "PhysicaA_Manuscript_Write_Read.pdf",
        "PhysicaA_Review_Write_Read.pdf",
        "PhysicaA_Supplement_Write_Read.pdf",
    ):
        return True
    if rel[-1] in ("SOURCE_README.md", "MANIFEST_SHA256.txt"):
        return True
    if rel[:2] == ("reports", "software_resources") and rel[-1] in (
        "journal_requirements.md", "publication_guidelines.md",
        "scientific_visualization_SKILL.md",
    ):
        return True
    return any(part.startswith(".") for part in rel)

def main():
    if len(sys.argv) not in (2, 3):
        raise SystemExit(__doc__)
    source = Path(sys.argv[1]).expanduser().resolve()
    target = Path(sys.argv[2]).expanduser().resolve() if len(sys.argv) == 3 else source.parent / TARGET_NAME
    if not source.is_file():
        raise SystemExit("Input archive not found: " + str(source))
    if source == target or target.exists():
        raise SystemExit("Output already exists or equals input; choose a new output path.")
    if sha_file(source) != INPUT_SHA256:
        raise SystemExit("Input SHA-256 differs from the saved verified release; refusing to modify it.")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".building")
    if temporary.exists():
        raise SystemExit("Temporary output exists; remove it or choose a new output path.")

    try:
        with zipfile.ZipFile(source, "r") as zin:
            corrupt = zin.testzip()
            if corrupt:
                raise ValueError("Input ZIP integrity check failed: " + corrupt)
            expected = json.loads(zin.read(HASH_LIST))
            if len(expected) != 102:
                raise ValueError("Expected hashes for 102 original result files.")
            for rel, digest in expected.items():
                name = ROOT + "reproducibility/" + rel
                if sha_bytes(zin.read(name)) != digest:
                    raise ValueError("Original result hash mismatch: " + rel)

            base_prefix = ROOT + "reproducibility/results/"
            graphs = sorted(
                name[len(base_prefix):-4] for name in zin.namelist()
                if name.startswith(base_prefix) and name.endswith(".npz")
                and "/" not in name[len(base_prefix):]
                and len(name[len(base_prefix):]) >= 3
                and name[len(base_prefix):len(base_prefix)+2].isdigit()
                and name[len(base_prefix)+2] == "_"
            )
            if len(graphs) != 32:
                raise ValueError("Expected 32 synthetic graph result files.")

            written = set()
            digest_lines = []
            with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as zout:
                def put(name, data):
                    if name in written:
                        raise ValueError("Duplicate output member: " + name)
                    written.add(name)
                    zout.writestr(name, data)
                    digest_lines.append((name[len(ROOT):], sha_bytes(data)))

                for info in zin.infolist():
                    if info.is_dir() or omitted(info.filename):
                        continue
                    data = zin.read(info.filename)
                    if info.filename == ROOT + "README.md":
                        data = README.encode("utf-8")
                    elif info.filename == ROOT + "reproduce.py":
                        old = b";call(P/'submission/make_letters.py')"
                        if data.count(old) != 1:
                            raise ValueError("Unexpected reproduction entry point.")
                        data = data.replace(old, b"")
                    elif info.filename == ROOT + "reports/software_resources/ACKNOWLEDGEMENTS.md":
                        data = data.replace(
                            b"Its MIT license and source snapshot accompany this release.",
                            b"Its MIT license is included and its public source is linked in resources_used.json.",
                        )
                    elif info.filename == ROOT + "reports/version_manifest.json":
                        meta = json.loads(data)
                        meta["own_dataset_doi_registration"] = "Not yet assigned"
                        meta["distribution"] = "Recovered self-contained code and data archive"
                        meta.pop("publication_action_performed", None)
                        if "manuscript_pdfs" in meta:
                            keep = ("PhysicaA_Manuscript_Write_Read.pdf",
                                    "PhysicaA_Review_Write_Read.pdf",
                                    "PhysicaA_Supplement_Write_Read.pdf")
                            meta["manuscript_pdfs"] = {
                                k: v for k, v in meta["manuscript_pdfs"].items() if k in keep
                            }
                        data = (json.dumps(meta, indent=2) + "\n").encode("utf-8")
                    put(info.filename, data)

                for graph in graphs:
                    name = REVIEW + "results/" + graph + "_strength.npz"
                    with np.load(io.BytesIO(zin.read(name)), allow_pickle=False) as merged:
                        if merged["loss"].shape != (3, 2, 3, 32, 4):
                            raise ValueError("Unexpected strength loss shape: " + graph)
                        if merged["dose"].shape != (3, 2, 3, 32, 5):
                            raise ValueError("Unexpected strength dose shape: " + graph)
                        if not np.array_equal(merged["strengths"], np.array([1.5, 3.0, 6.0])):
                            raise ValueError("Unexpected strength settings: " + graph)
                        for index, strength in ((0, 1.5), (2, 6.0)):
                            buf = io.BytesIO()
                            np.savez_compressed(
                                buf, loss=merged["loss"][index], dose=merged["dose"][index],
                                calls=np.array(1152), strength=np.array(strength),
                            )
                            put(REVIEW + "parts/" + graph + "_b" + format(strength, "g") + ".npz",
                                buf.getvalue())

                text = "".join(digest + "  " + name + "\n"
                               for name, digest in sorted(digest_lines))
                zout.writestr(ROOT + "MANIFEST_SHA256.txt", text.encode("utf-8"))

        with zipfile.ZipFile(temporary, "r") as verify:
            corrupt = verify.testzip()
            if corrupt:
                raise ValueError("Output ZIP integrity check failed: " + corrupt)
            for rel, digest in expected.items():
                if sha_bytes(verify.read(ROOT + "reproducibility/" + rel)) != digest:
                    raise ValueError("Output result hash mismatch: " + rel)
            for graph in graphs:
                with np.load(io.BytesIO(verify.read(REVIEW + "results/" + graph + "_strength.npz")),
                             allow_pickle=False) as merged:
                    for index, strength in ((0, 1.5), (2, 6.0)):
                        part_name = REVIEW + "parts/" + graph + "_b" + format(strength, "g") + ".npz"
                        with np.load(io.BytesIO(verify.read(part_name)), allow_pickle=False) as part:
                            if not np.array_equal(part["loss"], merged["loss"][index]):
                                raise ValueError("Recovered loss mismatch: " + part_name)
                            if not np.array_equal(part["dose"], merged["dose"][index]):
                                raise ValueError("Recovered dose mismatch: " + part_name)
            groups = [n for n in verify.namelist()
                      if "/interpretation/source_groups/" in n and n.endswith(".txt")]
            if len(groups) != 4:
                raise ValueError("Expected four school-group source files.")
        temporary.replace(target)
    except Exception:
        if temporary.exists():
            temporary.unlink()
        raise

    print("Created:", target)
    print("Output SHA-256:", sha_file(target))
    print("Original result files verified: 102")
    print("Recovered strength inputs verified: 64")
    print("The input archive was not modified.")

if __name__ == "__main__":
    main()
