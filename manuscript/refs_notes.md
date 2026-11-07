# refs.bib — verification notes

Companion note for `refs.bib` (manuscript: *How much validation evidence does an index selection need? Budget, sampler and the plateau in link-prediction benchmarks*).

## Totals

| Item | Count |
|---|---|
| Entries in `refs.bib` | **74** |
| Entries carrying a `doi` field | **63** |
| DOIs verified against **Crossref** (`api.crossref.org`) | **61** |
| DOIs that are arXiv/DataCite DOIs (not Crossref) | 2 |
| Entries with no DOI (canonical classics, books, dataset) | 11 |
| Duplicate keys | 0 |
| Duplicate works | 0 |

Validation performed: brace balance (0 net depth, no premature closes), ASCII-only
check (0 non-ASCII characters, so pdfLaTeX needs no `inputenc`/`fontenc` extras),
key-pattern check (`FirstAuthorYYYYKeyword`), required-field check per entry type,
duplicate-key and duplicate-DOI check. The file was also test-compiled end-to-end
with `pdflatex` + `bibtex` (`\nocite{*}`): bibtex reported zero warnings.

The two non-Crossref DOIs are `10.48550/arXiv.2005.00687` (OGB) and
`10.48550/arXiv.1811.05868` (Shchur et al.); both were verified through the arXiv
API and the DataCite registry (correct titles, author lists, years), because
neither is deposited with Crossref.

## The 9 entries without a DOI

| Key | Work | Why no DOI |
|---|---|---|
| `sorensen1948method` | Sorensen (1948), *Biologiske Skrifter* 5:1–34 | pre-DOI, not deposited |
| `salton1983introduction` | Salton & McGill (1983), McGraw-Hill | book, no DOI |
| `erdos1960evolution` | Erdős & Rényi (1960), *Publ. Math. Inst. Hungar. Acad. Sci.* 5:17–61 | pre-DOI |
| `knuth1993stanford` | Knuth (1993), *The Stanford GraphBase* | book, no DOI |
| `davis1941deep` | Davis, Gardner & Gardner (1941), *Deep South* | book, no DOI |
| `cawley2010overfitting` | Cawley & Talbot (2010), JMLR 11:2079–2107 | JMLR does not register DOIs |
| `demsar2006statistical` | Demšar (2006), JMLR 7:1–30 | JMLR does not register DOIs |
| `perlich2003tree` | Perlich, Provost & Simonoff (2003), JMLR 4:211–255 | JMLR does not register DOIs |
| `leskovec2014snap` | Leskovec & Krevl (2014), SNAP dataset collection | dataset landing page, no DOI |

For the three JMLR items, volume/page/year were confirmed directly on the JMLR
article pages (not guessed). Note that Perlich et al. ends on page **255**, not
231 as sometimes mis-cited.

## Corrections to the brief (Crossref used as source of truth)

1. **Lü & Zhou "Physics Reports"** — no such article exists in Crossref. The
   survey is *Physica A: Statistical Mechanics and its Applications* **390**(6):
   1150–1170 (2011), DOI `10.1016/j.physa.2010.11.027`.
2. **Yang, Lichtenwalter & Chawla "Data Mining and Knowledge Discovery"** — the
   paper appeared in *Knowledge and Information Systems* **45**(3):751–782 (2015),
   DOI `10.1007/s10115-014-0789-0`. No DMKD version was found.
3. **McAuley & Leskovec 2012** — the NeurIPS 2012 paper is not Crossref-indexed;
   the entry uses the journal version, *ACM TKDD* **8**(1):1–28 (2014),
   DOI `10.1145/2556612` (same work, "Discovering social circles in ego networks").
4. **Klimt & Yang 2004** — the CEAS-2004 "Introducing the Enron corpus" paper is
   not Crossref-indexed; the entry uses the peer-reviewed ECML 2004 paper on the
   same corpus, DOI `10.1007/978-3-540-30115-8_22`.
5. **Kotthoff 2016** — the canonical, DOI-verified survey is *AI Magazine*
   **35**(3):48–60 (2014), DOI `10.1609/aimag.v35i3.2460`; a 2016 LNCS chapter
   reprints it. The 2014 version is used.
6. **Ripeanu et al. 2002** — Crossref stores the authors with family/given names
   swapped ("Matei R.; Iamnitchi A.; Foster P."). Corrected in the entry to
   `Ripeanu, Matei and Iamnitchi, Adriana and Foster, Ian`.
7. **Wang, Xu, Wu et al.** — Crossref `issued` is 2014 (online first), but the
   print issue is *Science China Information Sciences* **58**(1), January 2015,
   which is the year used.
8. **Martínez et al.** — online 2016, print issue dated 2017; the entry uses 2016
   (the year the article became available and is normally cited).

## Gaps (topics from the brief with no fully verified reference)

1. **"Guo et al. on clustering-coefficient-based prediction."** No Crossref record
   with a matching title *and* first author "Guo" could be found for a
   clustering-coefficient link-prediction index (only minor 2021 conference papers
   where Guo is a later author, on signed networks). Substituted two verified
   works that cover the same ground: `wu2016link` (Wu, Lin, Wang & Gregory, 2016,
   *Physica A* 452:1–8) and `kumar2019level` (Kumar et al., 2019, *Applied
   Intelligence* 49(7):2762–2779).
2. **Dedicated study of "uniform vs. hard/structural negatives" in link
   prediction.** Searches for a paper whose title/author matched on this exact
   topic returned only training-side negative-sampling papers for graph
   embeddings/knowledge graphs (WSDM 2024, WWW 2024, etc.), not evaluation-side
   studies. The topic is instead covered indirectly by `yang2015evaluating`,
   `lichtenwalter2010new`, `japkowicz2002class`, `krichene2020sampled` (sampled
   metrics are biased and budget-dependent) and `mara2020benchmarking`. If the
   author wants a direct citation here, it should be supplied manually — no
   verified candidate was invented.
3. Minor: no separate verified entry for Sørensen's coefficient *as used in
   network science* (only the 1948 original); the original is included.

## Notes on field content

- DOIs are reproduced in the letter case returned by Crossref (DOIs are
  case-insensitive and resolve either way).
- `@misc` entries (`shchur2018pitfalls`, `leskovec2014snap`) carry `eprint`/
  `howpublished` rather than invented venue metadata.
- All author names are ASCII transliterations (Lu, Sorensen, Barabasi, Erdos,
  Guimera, Demsar, Gunnemann, Martinez, Renyi) as required for pdflatex.

## The ten references added in the revision (2021 and later)

Ten entries were added so that the evaluation-practice discussion cites
contemporary work rather than stopping in 2020. Each was checked against Crossref
(DOI, authors, venue, pages, year) before it was entered; the title of the
NeurIPS 2022 dynamic-graph paper is "Towards Better Evaluation for Dynamic Link
Prediction" (a shorter, differently worded title circulates informally and is not
used anywhere in the manuscript).

| Key | Venue and year | DOI |
|---|---|---|
| `li2023evaluating` | NeurIPS 2023 Datasets & Benchmarks, 3853-3866 | 10.52202/075280-0169 |
| `poursafaei2022towards` | NeurIPS 2022 Datasets & Benchmarks, 32928-32941 | 10.52202/068431-2386 |
| `huang2023tgb` | NeurIPS 2023, 2056-2073 | 10.52202/075280-0099 |
| `islam2022simple` | Studies in Computational Intelligence, 549-562 (2022) | 10.1007/978-3-030-93413-2_46 |
| `nguyen2024diffusion` | WWW '24, 948-958 | 10.1145/3589334.3645650 |
| `tiwari2021revisiting` | WWW '21, 809-820 | 10.1145/3442381.3449856 |
| `bi2024inconsistency` | PNAS Nexus 3(11), pgae498 | 10.1093/pnasnexus/pgae498 |
| `wan2025quantifying` | Chaos, Solitons & Fractals 199, 116864 | 10.1016/j.chaos.2025.116864 |
| `ma2025reconsidering` | CIKM '25, 2052-2062 | 10.1145/3746252.3761108 |
| `liang2026heuristics` | IEEE Transactions on Big Data 12(1), 1-14 | 10.1109/TBDATA.2025.3600031 |

They are cited in Section 2.2 (negative sampling and the pitfalls catalogues),
Section 2.4 (benchmarks) and in the limitations of Section 6.5 (metric
dependence). Reproduce the insertion with `scripts/add_refs_2021.py` and the
citations with `scripts/cite_new_refs.py`; the full verified BibTeX is in
`verified_linkprediction_refs.bib.md` at the workspace root used during the
revision.
