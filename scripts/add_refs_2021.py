"""Appends ten Crossref-verified 2021+ references to manuscript/refs.bib.

Every entry was verified against api.crossref.org and/or the NeurIPS proceedings
pages on 2026-11-07 (see verified_linkprediction_refs.bib.md).  Nothing here is
reconstructed from memory.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "manuscript" / "refs.bib"

ENTRIES = r"""
@inproceedings{li2023evaluating,
  author    = {Li, Juanhui and Shomer, Harry and Mao, Haitao and Zeng, Shenglai and Ma, Yao and Shah, Neil and Tang, Jiliang and Yin, Dawei},
  title     = {Evaluating Graph Neural Networks for Link Prediction: Current Pitfalls and New Benchmarking},
  booktitle = {Advances in Neural Information Processing Systems 36 (Datasets and Benchmarks Track)},
  year      = {2023},
  pages     = {3853--3866},
  doi       = {10.52202/075280-0169}
}

@inproceedings{poursafaei2022towards,
  author    = {Poursafaei, Farimah and Huang, Shenyang and Pelrine, Kellin and Rabbany, Reihaneh},
  title     = {Towards Better Evaluation for Dynamic Link Prediction},
  booktitle = {Advances in Neural Information Processing Systems 35 (Datasets and Benchmarks Track)},
  year      = {2022},
  pages     = {32928--32941},
  doi       = {10.52202/068431-2386}
}

@inproceedings{huang2023tgb,
  author    = {Huang, Shenyang and Poursafaei, Farimah and Danovitch, Jacob and Fey, Matthias and Hu, Weihua and Rossi, Emanuele and Leskovec, Jure and Bronstein, Michael and Rabusseau, Guillaume and Rabbany, Reihaneh},
  title     = {Temporal Graph Benchmark for Machine Learning on Temporal Graphs},
  booktitle = {Advances in Neural Information Processing Systems 36},
  year      = {2023},
  pages     = {2056--2073},
  doi       = {10.52202/075280-0099}
}

@incollection{islam2022simple,
  author    = {Islam, Md Kamrul and Aridhi, Sabeur and Smail-Tabbone, Malika},
  title     = {Simple Negative Sampling for Link Prediction in Knowledge Graphs},
  booktitle = {Complex Networks and Their Applications X},
  series    = {Studies in Computational Intelligence},
  publisher = {Springer},
  year      = {2022},
  pages     = {549--562},
  doi       = {10.1007/978-3-030-93413-2_46}
}

@inproceedings{nguyen2024diffusion,
  author    = {Nguyen, Trung-Kien and Fang, Yuan},
  title     = {Diffusion-based Negative Sampling on Graphs for Link Prediction},
  booktitle = {Proceedings of the ACM Web Conference 2024},
  year      = {2024},
  pages     = {948--958},
  doi       = {10.1145/3589334.3645650}
}

@inproceedings{tiwari2021revisiting,
  author    = {Tiwari, Sudhanshu and Bansal, Iti and Rivero, Carlos R.},
  title     = {Revisiting the Evaluation Protocol of Knowledge Graph Completion Methods for Link Prediction},
  booktitle = {Proceedings of the Web Conference 2021},
  year      = {2021},
  pages     = {809--820},
  doi       = {10.1145/3442381.3449856}
}

@article{bi2024inconsistency,
  author  = {Bi, Yilin and Jiao, Xinshan and Lee, Yan-Li and Zhou, Tao},
  title   = {Inconsistency among Evaluation Metrics in Link Prediction},
  journal = {PNAS Nexus},
  volume  = {3},
  number  = {11},
  pages   = {pgae498},
  year    = {2024},
  doi     = {10.1093/pnasnexus/pgae498}
}

@article{wan2025quantifying,
  author  = {Wan, Shuyan and Bi, Yilin and Jiao, Xinshan and Zhou, Tao},
  title   = {Quantifying Discriminability of Evaluation Metrics in Link Prediction for Real Networks},
  journal = {Chaos, Solitons and Fractals},
  volume  = {199},
  pages   = {116864},
  year    = {2025},
  doi     = {10.1016/j.chaos.2025.116864}
}

@inproceedings{ma2025reconsidering,
  author    = {Ma, Weishuo and Wang, Yanbo and Wang, Xiyuan and Zhang, Muhan},
  title     = {Reconsidering the Performance of {GAE} in Link Prediction},
  booktitle = {Proceedings of the 34th ACM International Conference on Information and Knowledge Management},
  year      = {2025},
  pages     = {2052--2062},
  doi       = {10.1145/3746252.3761108}
}

@article{liang2026heuristics,
  author  = {Liang, Shuming and Ding, Yu and Li, Zhidong and Liang, Bin and Zhang, Siqi and Wang, Yang and Chen, Fang},
  title   = {Can {GNNs} Learn Link Heuristics? A Concise Review and Evaluation of Link Prediction Methods},
  journal = {IEEE Transactions on Big Data},
  volume  = {12},
  number  = {1},
  pages   = {1--14},
  year    = {2026},
  doi     = {10.1109/TBDATA.2025.3600031}
}
"""

text = BIB.read_text(encoding="utf-8")
for key in ["li2023evaluating", "poursafaei2022towards", "huang2023tgb",
            "islam2022simple", "nguyen2024diffusion", "tiwari2021revisiting",
            "bi2024inconsistency", "wan2025quantifying", "ma2025reconsidering",
            "liang2026heuristics"]:
    assert key not in text, f"{key} already present"
BIB.write_text(text.rstrip() + "\n" + ENTRIES, encoding="utf-8")
print("appended 10 entries;", BIB.read_text(encoding='utf-8').count("\n@"), "total")