"""Standardize panel identifiers in existing vector PDFs without redrawing data.

Run after the journal/study figures are exported. Geometry is unchanged; only
the existing (a), (b), ... text identifiers are replaced. The mechanism figure
uses equivalent identifiers in its native SVG reconstruction script.

python standardize_panel_labels.py --source-dir PATH --main-tex PATH --supplement-tex PATH
"""
from pathlib import Path
import argparse
import json
import re

import fitz
from matplotlib.font_manager import FontProperties, findfont


def placements(tex, text_width):
    matches = re.findall(r"\\includegraphics\[width=([.\d]*)\\textwidth\]\{([^}]+)\}", tex.read_text())
    return [(name if name.endswith(".pdf") else name + ".pdf", float(factor or 1) * text_width)
            for factor, name in matches]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--main-tex", type=Path, required=True)
    parser.add_argument("--supplement-tex", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    fontfile = findfont(FontProperties(family="DejaVu Sans", weight="bold"))
    font = fitz.Font(fontfile=fontfile)
    targets = placements(args.main_tex, 522 * 72 / 72.27)
    targets += placements(args.supplement_tex, (210 - 44) * 72 / 25.4)
    report = []
    for name, output_width in targets:
        path = args.source_dir / name
        if name == "mechanism_reference_vector.pdf":
            continue
        doc = fitz.open(path)
        page = doc[0]
        scale = output_width / page.rect.width
        size = 9 / scale
        operations = []
        for block in page.get_text("rawdict")["blocks"]:
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    chars = span.get("chars", [])
                    text = "".join(c["c"] for c in chars)
                    match = re.match(r"^\([a-d]\)", text)
                    if not match:
                        continue
                    label = match.group()
                    rectangle = fitz.Rect(chars[0]["bbox"])
                    for char in chars[1:3]:
                        rectangle |= fitz.Rect(char["bbox"])
                    origin = list(chars[0]["origin"])
                    title = next((c for c in chars[3:] if not c["c"].isspace()), None)
                    if title:
                        available = title["bbox"][0] - 2
                        origin[0] = min(origin[0], available - font.text_length(label, fontsize=size))
                    operations.append((label, rectangle, origin))
        remove_single = len(operations) == 1
        for label, rectangle, origin in operations:
            page.add_redact_annot(rectangle + (-0.05, -0.05, 0.05, 0.05), fill=False)
        if operations:
            # Keep all paths, markers and images. Remove only overlapping text.
            page.apply_redactions(images=0, graphics=0, text=0)
            if not remove_single:
                for label, rectangle, origin in operations:
                    page.insert_text(origin, label, fontsize=size, fontname="JCSPanelBold",
                                     fontfile=fontfile, color=(0, 0, 0))
            temp = path.with_name(path.stem + "_panel_tmp.pdf")
            doc.save(temp, garbage=4, deflate=True)
            doc.close()
            temp.replace(path)
        else:
            doc.close()
        report.append(dict(file=name, source_width=round(output_width / scale, 5),
                           rendered_width=round(output_width, 5),
                           source_font_size=round(size, 6), rendered_panel_size=9,
                           panel_labels=[] if remove_single else [q[0] for q in operations],
                           removed_redundant_single_panel_label=remove_single))
    args.manifest.write_text(json.dumps(report, indent=2) + "\n")
    print("PASS:", sum(len(r["panel_labels"]) for r in report),
          "panel identifiers standardized at 9 pt; data paths and markers retained.")


if __name__ == "__main__":
    main()
