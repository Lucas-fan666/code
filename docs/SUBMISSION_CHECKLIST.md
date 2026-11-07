# Pre-submission checklist

Work top to bottom. Items marked **[author]** require information only the author
have; everything else is already done in this package.

## Current build facts (verify, do not retype)

| Item | Current value |
|---|---|
| Class | local single-column `comjnl.cls` shim (official OUP class to be dropped in) |
| Pages | 31 |
| Tables | 18 |
| Figures | 12 (vector PDF + 300 dpi PNG) |
| References | 64 entries in `manuscript/refs.bib`; 53 carry a DOI |
| Undefined references | 0 |
| Undefined citations | 0 |
| Overfull `\hbox` warnings | 0 |
| Abstract | check length against the journal's limit |
| Keywords | 6 |

## A. Manuscript content

- [x] Author block complete: single author, affiliation, e-mail and ORCID
      iD 0009-0006-9624-385X (see `docs/AUTHOR_INFO_PLACEHOLDERS.md`)
- [x] `\received` and `\revised` set to 7 November 2026; production replaces
      the stamp with the actual submission and revision dates
- [x] Funding: "This research received no external funding."; competing
      interests: none to declare
- [x] CRediT roles spelled out in the Declarations **[author to confirm roles]**
- [x] AI-use statement pasted from `docs/AI_DISCLOSURE.md` (adopted version:
      language editing and small code modifications)
- [ ] Confirm the author order, corresponding author and `\shortauthors`
      (`J. Fan \textit{et al.}` is already set) **[author]**
- [ ] Check that every coauthor affiliation is represented. The shim has a
      single `\affiliation`; the official class may accept several, so re-check
      after the class swap **[author]**
- [ ] Read the compiled PDF end to end once for style (the numbers are final)
- [ ] Confirm the abstract is within the journal's word limit (verify against
      the current PDF; the abstract was revised with the new results)
- [ ] Confirm the keyword count (current: 6)
- [ ] Decide whether Appendix A stays in the paper or moves to a supplement

## B. Build and files

- [ ] `cd manuscript && pdflatex main && bibtex main && pdflatex main && pdflatex main`
      (MiKTeX: the same four passes; see `docs/SUBMISSION_GUIDE.md` Section 3)
- [ ] Confirm **zero undefined references**, **zero undefined citations** and
      **zero overfull `\hbox` warnings**. The last shim build has all three at
      zero.
- [ ] Confirm the PDF opens cleanly and the page count is **31** at the shim
      build. Record any change after swapping in the official class.
- [ ] Confirm the table count is 18 and the figure count is 12.
- [ ] Regenerate all main tables/figures from scratch once and diff:
      `python scripts/analyze_results.py && python scripts/make_figures.py`
- [ ] Regenerate the supplementary experiments in the order given in
      `docs/SUBMISSION_GUIDE.md` Section 6, then rebuild the manuscript.
- [ ] Confirm `results/key_numbers.json` and `results/new_key_numbers.json` still
      match the numbers in the text (map in `docs/FINAL_FINDINGS.md`).
- [ ] Confirm the 23-network caveat appears wherever a supplementary pooled
      number is quoted (Florentine is excluded).

## C. Journal-specific package

- [ ] Download the OUP author kit for *The Computer Journal* and drop the
      official `comjnl.cls` and `compj.bst` into `manuscript/`
      **[author]** (network access needed)
- [ ] Remove or archive the local shim `comjnl.cls`, and change
      `\bibliographystyle{plainnat}` to `\bibliographystyle{compj}`
- [ ] Rebuild with the official class and confirm the metadata macros still work
      (`\title[short]`, `\author`, `\affiliation`, `\email`, `\shortauthors`,
      `\received`, `\revised`, `\keywords`)
- [ ] Confirm fees and open-access route in writing on the OUP journal page
      **[author]**
- [ ] Prepare the highlights file from `docs/HIGHLIGHTS.md` if the portal asks
      (both sets are within 85 characters per bullet)
- [ ] Prepare a graphical abstract only if the portal asks; Figure 1 is a
      suitable candidate
- [ ] Add line numbers if the journal asks (`\usepackage[switch]{lineno}` and
      `\linenumbers`)
- [ ] Check figure resolution: all figures are vector PDF plus 300 dpi PNG
- [ ] Check colour-figure charges if any figure will appear in print
      **[author]**
- [ ] Check that the single-column measure of the official class does not
      overfull any of the 25 tables

## D. References

- [ ] 64 entries in `manuscript/refs.bib`; 53 carry a DOI
- [ ] `manuscript/refs_notes.md` records the earlier 60-entry/51-DOI state. It is
      stale; re-resolve the entries added since it was written, or refresh the
      note before archiving **[author]**
- [ ] Check that every reference is cited in the text and vice versa
      (`bibtex` warnings are the quick check; the last build has none)
- [ ] Confirm the official `compj.bst` produces author-year citations that match
      the `\citep`/`\citet` commands already in the text

## E. Integrity and availability

- [ ] Run the journal's (or institution's) similarity check **[author]**
- [ ] Confirm no figure or table is duplicated from another publication
      (all are generated for this paper)
- [ ] Deposit the code and derived data in a repository and obtain a DOI
      (Zenodo/figshare; the package is self-contained) **[author]**
- [ ] Update the Data/Code availability statements with that DOI **[author]**
- [ ] Confirm the SNAP terms of use permit redistribution of the derived edge
      lists, or ship only the download script and checksums **[author]**
- [ ] Confirm that `tools/how_much_validation.py` runs from a clean environment
      with only `numpy` and `pandas` (no network access)

## F. Submission portal

- [ ] Cover letter adapted from `docs/COVER_LETTER.md` **[author]**
- [x] Suggested reviewers: none supplied; the cover letter states that the author
      leaves the choice of referees to the Editor
- [x] ORCID iD linked: 0009-0006-9624-385X (title page and cover letter)
- [ ] Manuscript, figures, highlights and supplement uploaded in the portal's
      required order
- [ ] Keep a copy of the submitted PDF and the confirmation e-mail

## G. After submission

- [ ] Note the manuscript ID and the date
- [ ] Archive `results/raw_results.csv` and `results/method_scores.csv` together
      with `results/key_numbers.json` and `results/new_key_numbers.json`; they
      are the evidence base for every number in the paper and are far cheaper to
      store than to regenerate
- [ ] Archive `results/pilot_scores.csv` and `results/floor_cells.csv` if the
      released tool is to remain runnable on the examples in `tools/README.md`
