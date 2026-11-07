# Author information and placeholders

The metadata that the author can supply without inventing anything is now filled
in. What remains unfilled is listed in Section 1 and consists only of identifiers
that must be obtained from outside the package (ORCID, reviewer suggestions,
editorial dates).

## 1. Title page and declarations (done)

| Field | Current value |
|---|---|
| Title | How much validation evidence does an index selection need? Budget, sampler and the plateau in link-prediction benchmarks |
| Short title | `Validation budget and sampler` |
| Author | Junkai Fan |
| Affiliation | School of Business Administration, Northeastern University, Shenyang 110167, China |
| E-mail | fanjk@mails.neu.edu.cn |
| ORCID | 0009-0006-9624-385X |
| Short authors | `J. Fan` |
| Received / revised | 7 November 2026 / 7 November 2026 |
| Funding | This research received no external funding. |
| Competing interests | The author has no competing interests to declare. |
| Author contributions | Junkai Fan is the sole author and performed all roles (CRediT list spelled out in the Declarations). |
| Use of generative AI | Language editing and small modifications to analysis and figure code only; see `docs/AI_DISCLOSURE.md`. |

`\shortauthors` is set to `J. Fan` for a single-author submission. If coauthors
are added, extend both `\author` and `\shortauthors` and check that the local
shim's single `\affiliation` still matches the official OUP class.

## 2. Still to be supplied by the author

Reviewer suggestions: none (the author declines; the cover letter states this).
ORCID: supplied above. Remaining items:

| Item | Where | Why it is not filled in |
|---|---|---|
| Editorial dates | title page | OUP stamps these; 7 November 2026 is used until the office replaces it. |

## 3. Cover letter

`docs/COVER_LETTER.md` is complete: it carries the date, the no-funding
statement, the ORCID line and an explicit statement that no reviewer suggestions
are made. The signature block carries Junkai Fan's name, affiliation and e-mail.

## 4. Optional metadata

- **CRediT taxonomy** roles follow the standard NISO list.
- **Acknowledgements**: none. Add an `\paragraph{Acknowledgements.}` before the
  Declarations if that changes.
- **Supplementary material**: the package already contains the 24-network
  comparison (Appendix A), the average-precision table (Appendix B) and the
  per-network table (Appendix C), plus the candidate-set-size and composition
  experiments (Sections 5.13-5.14). If the journal wants a separate supplement,
  move Appendices A-C plus `results/per_graph.csv` and
  `results/candidate_size_summary.csv` into it.

## 5. What is *not* a placeholder

Every number, table, figure and citation in the manuscript is final and traceable
to `results/` and `tables/` (see `docs/FINAL_FINDINGS.md`). No result is
provisional. The only unfilled content is the list in Section 2.
