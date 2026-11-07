# Data and code availability: what is deposited where

The journal requires a Data Availability Statement. This package satisfies it
with two deposits:

| Deposit | Content | Built by |
|---|---|---|
| Zenodo, DOI [10.5281/zenodo.24035480](https://doi.org/10.5281/zenodo.24035480) | `data_package.zip` (processed edge lists, temporal tables, manifests) and `code_package.zip` (code, results, tables, figures, tools, docs) | `scripts/make_zenodo.py` |
| GitHub, [https://github.com/Lucas-fan666/code](https://github.com/Lucas-fan666/code), branch `replication-package-v1.0.0` | the same tree under version control, MIT licence | `scripts/git_push.py` |

The manuscript statement in `manuscript/main.tex` (`\paragraph{Data availability}`,
line 698, and `\paragraph{Code availability}`, line 700) cites both.

## 1. Zenodo (done)

Record: https://doi.org/10.5281/zenodo.24035480

Everything is reproducible from `dist/zenodo/`:

| File | Purpose |
|---|---|
| `README_DEPOSIT.md` | the upload sheet: every form field, in order |
| `metadata.json` | the same fields as JSON, for the Zenodo REST API or for pasting |
| `data_package.zip` | data to upload (12.9 MB) |
| `code_package.zip` | code and results to upload (8.8 MB) |
| `zenodo_deposit.zip` | all of the above plus `manuscript.pdf`, for a single drop |
| `CHECKSUMS.md5` | MD5 of each file, for Zenodo's checksum column |

If the record must be revised, run `python scripts/make_zenodo.py` and upload a
new version; Zenodo keeps the concept DOI pointing at the newest version.

## 2. GitHub (branch `replication-package-v1.0.0`)

`scripts/git_push.py` commits the whole tree to a new branch of
`Lucas-fan666/code` without touching `main`. It needs a personal access token
with the `repo` scope for one run:

    python scripts/git_push.py --token ghp_xxx [--branch replication-package-v1.0.0]

Steps it performs: `git init` in the package root, `git add` of the whitelisted
files (`.gitignore` keeps `data/raw`, `data/processed`, build artefacts and
`__pycache__` out), a single commit, then a path-scoped push

    git push https://<token>@github.com/Lucas-fan666/code HEAD:replication-package-v1.0.0

The push URL is assembled at run time, so the token never enters `.git/config`.

Afterwards, open a pull request from `replication-package-v1.0.0` into `main` if the repository
should adopt the package wholesale, or leave the branch as the citable
snapshot and tag it `v1.0.0`.
