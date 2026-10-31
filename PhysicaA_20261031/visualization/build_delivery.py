"""Assemble the validated visual revision; does not alter scientific inputs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import csv
import hashlib
import io
import json
import re
import shutil
import sys

import fitz

R=Path(__file__).resolve().parents[1]
O=R.parent/'output'
O.mkdir(exist_ok=True)
M=R/'manuscript'
V=R/'visualization/exports'
REP=R/'reports'
inventory=json.loads((REP/'visual_revision/figure_inventory.json').read_text())
names={x['name'] for x in inventory['figures']}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def copy(source, target):
    payload=source.read_bytes()
    staged=target.with_name(target.name+'.installing')
    staged.write_bytes(payload)
    staged.replace(target)
    assert target.read_bytes()==payload,target


def visible(p):
    return p.is_file() and not p.name.startswith('.') and not p.name.endswith('.installing')


def archive(path, files):
    stream=io.BytesIO()
    with ZipFile(stream,'w',ZIP_DEFLATED,compresslevel=6) as z:
        for source,target in sorted(files,key=lambda x:x[1]):
            z.writestr(target,source.read_bytes())
    staged=path.with_name(path.name+'.installing')
    staged.write_bytes(stream.getvalue());staged.replace(path)
    with ZipFile(path) as z:
        assert z.testzip() is None


def audit_figures():
    rows=[]
    for row in inventory['figures']:
        p=V/(row['name']+'.pdf')
        assert p.read_bytes().rstrip().endswith(b'%%EOF'),p
        with fitz.open(p) as doc:
            assert len(doc)==1
            rasters=sum(len(page.get_images(full=True)) for page in doc)
        svg=(V/(row['name']+'.svg')).read_text()
        assert rasters==0 and '<image' not in svg,p
        for ext in ['pdf','svg','png']:
            q=V/(row['name']+'.'+ext)
            assert sha(q)==row['files'][ext]['sha256'],q
        rows.append(dict(figure=row['name'],embedded_raster_images=rasters,svg_text_editable='<text' in svg))
    (REP/'visual_revision/vector_checks.json').write_text(json.dumps(rows,indent=2))
    return rows


def guide_and_report(vector_rows):
    # Use the current editorial records, rather than frozen prose from an older revision.
    current_guide=REP/'PhysicaA_Figure_Style_Guide.md'
    current_report=REP/'PhysicaA_Visual_Revision_Report.md'
    if current_guide.exists() and current_report.exists():
        copy(current_guide,O/current_guide.name)
        copy(current_report,O/current_report.name)
        copy(REP/'visual_revision/figure_inventory.json',O/'PhysicaA_Figure_Inventory.json')
        copy(REP/'PhysicaA_Editorial_Review.md',O/'PhysicaA_Editorial_Review.md')
        copy(REP/'visual_revision/figure_inventory.json',REP/'PhysicaA_Figure_Inventory.json')
        return
    guide='''# Physica A figure style

All 29 cited figures are exported as native vector PDF, editable SVG and 300 dpi PNG. The first nine belong to the main text; the remaining twenty to the Supplement. Figure numbering follows the order in the compiled manuscripts. PhysicaA_Figure_Inventory.json maps each exported asset to its numerical source.

| Role | Color |
|---|---|
| Rumor / positive initial memory | #B23A48 |
| Correction / ordered reset estimator | #087F8C |
| Inactive state / neutral reference | #7B8693 |
| Correction target / auxiliary branch | #C59424 |
| Common reaction paths (RTC) | #3569A8 |
| Global thinning | #B36746 |
| Antithetic thinning | #756AA3 |
| Text and axes | #243547 |

Figures use DejaVu Sans, white backgrounds, open axes and light grids. Data-chart text is at least 8 pt in the source artwork; final print size depends on the placement width. Curves also differ in line style and marker shape. Red/white/teal heat maps use a shared linear scale centered at zero for signed contrasts. Nonnegative response maps use a light-to-dark teal/navy scale. Color-bar cells and chart elements remain vector.

Uncertainty conventions are stated in each caption. One-standard-error bands, descriptive 95% intervals, adjusted inferential intervals and interquartile ranges keep their original meanings. No figure transformation changes the plotted numerical values or the comparison family. Full grids and unfavorable comparisons remain included.

To redraw from saved outputs: `python3 visualization/render_all.py` in PhysicaA_20261031. The common style is in visualization/theme.py. The separate LaTeX source ZIP compiles without simulation data.
'''
    (O/'PhysicaA_Figure_Style_Guide.md').write_text(guide)
    report='''# Physica A visual revision

The main text now has nine figures and the Supplement twenty. Four existing figures were returned to the main text: matched initial-memory response, static/zero/dynamic memory and relaxation time scales, naturally generated memory and feedback, and the empirical slack of variance bounds. They connect the physical response experiments to the comparison theory.

All 29 figures were redrawn from saved outputs with a shared palette, font, line weight and panel-label style. Nearby curves use line styles and markers as well as color. The cost-quality display now separates the graphical/RTC pair from the thinning/antithetic pair into four panels, with the column-specific vertical ranges stated in the caption. Heat maps show all original cells and explicit linear color scales. The four-panel mechanism remains a programmatically drawn vector illustration.

No new propagation experiment or inferential comparison was run. Byte comparison found no difference in the 73 checked files from the raw-data package or the 111 checked numerical/configuration/scientific-code files from the previous code package. All 28 proof blocks match after the documented normalization. Figure captions and cross-document references were updated to match the new placement.

The compiled main text has 14 pages, the Supplement 54 and the optional single-column copy 29. The 208-word abstract, five Highlights and 74-entry reference set are unchanged. Final LaTeX logs contain no undefined references or overfull boxes. The main text and figure previews were visually inspected after compilation. A fresh extraction of the code and unchanged data packages redrew all 29 figures and compiled all three PDFs with no undefined references or overfull boxes. Every figure PDF and SVG has zero embedded raster images; PNG copies are supplied separately for convenience.

This revision changes presentation and placement. It does not alter the scientific claims, parameters, seeds, confidence levels, graph inclusion rules or interpretation of uncertain results. The assigned Zenodo record still requires the author's publication step; the archive instructions distinguish the current visual revision from byte-preserved historical data.
'''
    (O/'PhysicaA_Visual_Revision_Report.md').write_text(report)
    shutil.copy2(REP/'visual_revision/figure_inventory.json',O/'PhysicaA_Figure_Inventory.json')
    for name in ['PhysicaA_Figure_Style_Guide.md','PhysicaA_Visual_Revision_Report.md','PhysicaA_Figure_Inventory.json']:
        copy(O/name,REP/name)


def atlas():
    doc=fitz.open()
    for row in inventory['figures']:
        page=doc.new_page(width=842,height=595)
        designation=f"Main Figure {row['number']}" if row['document']=='Main' else f"Supplementary Figure S{row['number']}"
        page.insert_text((28,27),designation,fontsize=14,fontname='hebo',color=(.14,.21,.28))
        page.insert_text((28,45),row['name']+'.pdf',fontsize=9,fontname='helv',color=(.40,.46,.52))
        with fitz.open(V/(row['name']+'.pdf')) as src:
            page.show_pdf_page(fitz.Rect(28,63,814,551),src,0,keep_proportion=True)
        page.insert_text((28,577),'Physica A visual revision | Saved numerical outputs; original uncertainty conventions',fontsize=8,fontname='helv',color=(.40,.46,.52))
    doc.set_metadata(dict(title='Physica A figure atlas',author='Junkai Fan',subject='Nine main and twenty supplementary figures'))
    doc.save(O/'PhysicaA_Figure_Atlas.pdf',garbage=4,deflate=True)
    assert len(fitz.open(O/'PhysicaA_Figure_Atlas.pdf'))==29


def source_files():
    extra={'build.py','README.txt','main_labels.tex','supplement_labels.tex','main.bbl','supplement.bbl'}
    for p in M.iterdir():
        if not visible(p):continue
        if p.name in extra or (p.suffix in {'.tex','.bib','.bst','.cls','.sty'} and p.name!='main_review.tex') or (p.suffix in {'.pdf','.svg'} and p.stem in names):
            yield p


def code_files():
    for p in R.rglob('*'):
        if not p.is_file():continue
        rel=p.relative_to(R)
        if any(x.startswith('.') or x in {'__pycache__','tmp','submission','exports','figures','source','plot_data'} for x in rel.parts):continue
        if rel.parts[0]=='data_sources' or p.suffix in {'.npz','.tar','.gz','.zip','.eps','.png'}:continue
        if rel.parts[0]=='manuscript':continue
        if p.suffix not in {'.py','.cpp','.h','.hpp','.json','.csv','.sha256','.md','.txt','.cff','.tex'}:continue
        if p.name in {'main_before.tex','supplement_before.tex','readable_export_input.tex'} or p.name.startswith('before_'):continue
        if p.name in {'github_payload.json','github_base_files.json','github_text_candidates.json'}:continue
        yield p
    yield from source_files()


def assemble():
    vector_rows=audit_figures()
    guide_and_report(vector_rows)
    atlas()
    for source,target in [('main.pdf','PhysicaA_Manuscript.pdf'),('supplement.pdf','PhysicaA_Supplement.pdf'),('main_review.pdf','PhysicaA_Single_Column.pdf')]:
        copy(M/source,O/target)
    for p in (R/'submission_files').iterdir():
        if visible(p):copy(p,O/p.name)
    for name in ['PhysicaA_Final_Validation.json','PhysicaA_Number_Lineage.csv']:
        copy(REP/name,O/name)
    figure_files=[]
    for row in inventory['figures']:
        folder='Main' if row['document']=='Main' else 'Supplement'
        number=f"{row['number']:02d}" if folder=='Main' else f"S{row['number']:02d}"
        for ext in ['pdf','svg','png']:
            figure_files.append((V/(row['name']+'.'+ext),f"{folder}/{number}_{row['name']}.{ext}"))
    for name in ['PhysicaA_Figure_Style_Guide.md','PhysicaA_Figure_Inventory.json','PhysicaA_Visual_Revision_Report.md']:
        figure_files.append((O/name,name))
    archive(O/'PhysicaA_Figures.zip',figure_files)
    archive(O/'PhysicaA_LaTeX_Source.zip',[(p,p.name) for p in source_files()])
    code=list(code_files())
    hashes={str(p.relative_to(R)):sha(p) for p in code if p.suffix in {'.py','.cpp','.h','.hpp','.sha256','.cff','.tex','.bib','.bst','.cls','.sty'} and p.name!='PhysicaA_Source_SHA256.json'}
    (REP/'PhysicaA_Source_SHA256.json').write_text(json.dumps(hashes,indent=2))
    if REP/'PhysicaA_Source_SHA256.json' not in code:code.append(REP/'PhysicaA_Source_SHA256.json')
    archive(O/'PhysicaA_Reproducibility_Code.zip',[(p,'PhysicaA_20261031/'+str(p.relative_to(R))) for p in code])
    submission_names=['PhysicaA_Manuscript.pdf','PhysicaA_Supplement.pdf','PhysicaA_LaTeX_Source.zip','PhysicaA_Highlights.txt','PhysicaA_Cover_Letter.txt','PhysicaA_CRediT.txt','PhysicaA_Declarations.txt','PhysicaA_Submission_Guide.txt']
    archive(O/'PhysicaA_Submission_Package.zip',[(O/n,n) for n in submission_names])
    previous=Path(sys.argv[1])
    stage=R.parent/'zenodo_current_visual_final'
    with ZipFile(previous) as z:z.extractall(stage)
    root=stage/'PhysicaA_Zenodo_Upload'
    old=list(csv.DictReader((root/'PhysicaA_Manifest.csv').open()))
    historical=[x for x in old if x['file'].startswith('PhysicaA_Original_')]
    for p in O.iterdir():
        if visible(p) and p.name not in {'PhysicaA_Zenodo_Upload_Part1_Current.zip','PhysicaA_Submission_Package.zip'}:
            copy(p,root/p.name)
    for name in ['PhysicaA_Source_SHA256.json','PhysicaA_Final_Validation.json','PhysicaA_Number_Lineage.csv','PhysicaA_Fresh_Extraction_Validation.json','claim_evidence_matrix.csv']:
        copy(REP/name,root/name)
    readme=root/'PhysicaA_Archive_README.md'
    text=readme.read_text().split('## Visual revision')[0]+'## Visual revision\n\nThe current manuscript has nine main and twenty supplementary figures. All 29 native vector PDF/SVG and 300 dpi PNG copies, a figure atlas, shared style and source inventory are included. The editorial review records notation repairs, language changes and descriptive display calculations. The raw Physical_Response_Data ZIP and the twelve historical archives are unchanged. This Part 1 replaces the previous current transport part; continue to use the unchanged historical Part 2. The code ZIP contains the complete figure inputs and revised authoring code; the original scientific commit identifies the unchanged simulation implementation.\n'
    readme.write_text(text)
    rows=historical+[{ 'file':p.name,'bytes':len(p.read_bytes()),'sha256':sha(p)} for p in root.iterdir() if visible(p) and p.name not in {'PhysicaA_Manifest.csv','PhysicaA_SHA256SUMS.txt'}]
    rows.sort(key=lambda x:x['file'])
    with (root/'PhysicaA_Manifest.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['file','bytes','sha256']);w.writeheader();w.writerows(rows)
    (root/'PhysicaA_SHA256SUMS.txt').write_text(''.join(f"{x['sha256']}  {x['file']}\n" for x in rows))
    archive(O/'PhysicaA_Zenodo_Upload_Part1_Current.zip',[(p,'PhysicaA_Zenodo_Upload/'+p.name) for p in root.iterdir() if visible(p)])
    print(json.dumps({p.name:dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(O.iterdir()) if visible(p)},indent=2))


if __name__=='__main__':assemble()
