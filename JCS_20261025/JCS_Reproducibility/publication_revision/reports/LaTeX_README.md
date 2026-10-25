# Compile the manuscript

Run `python build_documents.py` with pdflatex, BibTeX and pypdf installed. The script builds both documents in a clean temporary directory using the bundled newtx font files. Build the main manuscript before the supplement because the latter imports main-document labels. The supplied class is the official FCS research class; it is unchanged.

The biography uses the supplied photo and appears after the references. All figure PDFs are vector originals where available. No shell escape or online data download is required. Final outputs are also supplied in the submission archive.
