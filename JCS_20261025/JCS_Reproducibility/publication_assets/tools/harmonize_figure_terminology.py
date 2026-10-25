"""Apply the manuscript's names to existing vector figure text.

Only the three requested headings/legend entries are changed. Numerical text,
drawing paths, panel identifiers, font sizes and figure geometry are retained.
"""
from pathlib import Path
import argparse
import json
import re

import fitz
from matplotlib.font_manager import FontProperties, findfont

REPLACEMENTS = {
    "confirmation.pdf": {
        "FEX vs node exchange": "FEX vs NEX",
        "FEX vs node greedy": "FEX vs greedy",
    },
    "cost_accuracy.pdf": {"Common reaction paths": "RTC (global)"},
}


def paths(page):
    keys = ["items", "type", "closePath", "fill", "color", "width", "fill_opacity",
            "stroke_opacity", "lineCap", "lineJoin", "dashes", "rect"]
    return json.dumps([{k: d.get(k) for k in keys} for d in page.get_drawings()],
                      default=str, sort_keys=True)


def numbers(page):
    return re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", page.get_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    report = []
    for filename, replacements in REPLACEMENTS.items():
        path = args.source_dir / filename
        doc = fitz.open(path)
        page = doc[0]
        before_numbers, before_paths = numbers(page), paths(page)
        operations = []
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line["spans"]:
                    chars = span["chars"]
                    text = "".join(c["c"] for c in chars)
                    for old, new in replacements.items():
                        if old not in text:
                            continue
                        start = text.index(old)
                        selected = chars[start:start + len(old)]
                        rectangle = fitz.Rect(selected[0]["bbox"])
                        for char in selected[1:]:
                            rectangle |= fitz.Rect(char["bbox"])
                        operations.append(dict(old=old, new=new, bbox=rectangle,
                                               origin=selected[0]["origin"], size=span["size"],
                                               bold="Bold" in span["font"], color=span["color"]))
        for op in operations:
            page.add_redact_annot(op["bbox"], fill=False)
        if operations:
            page.apply_redactions(images=0, graphics=0, text=0)
            for op in operations:
                fontfile = findfont(FontProperties(family="DejaVu Sans", weight="bold" if op["bold"] else "normal"))
                color = tuple(((op["color"] >> n) & 255) / 255 for n in [16, 8, 0])
                page.insert_text(op["origin"], op["new"], fontsize=op["size"],
                                 fontname="JCSTermBold" if op["bold"] else "JCSTermRegular",
                                 fontfile=fontfile, color=color)
            temporary = path.with_name(path.stem + "_terms_tmp.pdf")
            doc.save(temporary, garbage=4, deflate=True)
            doc.close()
            temporary.replace(path)
            doc = fitz.open(path)
            page = doc[0]
        assert before_numbers == numbers(page), (filename, "numerical text")
        assert before_paths == paths(page), (filename, "drawing paths")
        text = page.get_text()
        for old, new in replacements.items():
            assert old not in text and new in text, (filename, old, new)
        report.append(dict(file=filename, replacements=[dict(before=o["old"], after=o["new"]) for o in operations],
                           numbers_unchanged=True, all_drawing_paths_unchanged=True))
        doc.close()
    args.manifest.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS:", sum(len(r["replacements"]) for r in report), "terminology edits; numerical text and drawing paths unchanged.")


if __name__ == "__main__":
    main()
