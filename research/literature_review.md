# Literature landscape (living review)

Last updated: 2026-08-20

## Summary

The field has progressed beyond affinity-only peptide–MHC prediction toward presentation, immunogenicity and integrated patient-level selection. The public software landscape is heterogeneous: some projects expose peptide–HLA scores, while others consume VCF/BAM/RNA-seq data and combine variant expression, clonality, similarity, processing and binding features. These task differences make a single undifferentiated leaderboard scientifically invalid.

TESLA established prospective, patient-specific comparison across six subjects and 25 evaluable teams, with 608 tested peptide–MHC candidates and 37 detected immune responses. It also established that ranking and candidate-recovery metrics measure related but distinct properties. The 2023 ITSNdb study added a curated set of 199 presented MHC-I neoantigens with positive and negative immune assays and compared seven software families. NeoHunter subsequently reported patient-wise TESLA ranking metrics. These studies mean NeoRepro cannot claim novelty for patient-level Top-K evaluation alone.

Recent model papers and benchmarks further complicate naive comparisons. BigMHC released presentation and immunogenicity models with public code/data. NeoGuider reports seven-cohort patient evaluation. A 2026 Cell Genomics study demonstrates severe HLA-label shortcut behavior, including strong HLA-only baselines. TransNRank reports improved Top-20 recall on NCI, TESLA and HiTIDE, while NEAT predicts expert vaccine-board decisions rather than functional T-cell immunogenicity.

The 2024 IMPROVE study contributes a particularly useful evaluation resource: 17,520 patient-matched T-cell screening outcomes from 70 patients across metastatic melanoma, metastatic urothelial carcinoma and a pan-cancer basket cohort. Its public repository preserves patient, cohort, peptide and HLA fields. NeoRepro uses these records as the principal benchmark only after an independent exact-overlap audit against the official PRIME2 training table.

The remaining practical gap is longitudinal reproducibility and fair rerunning. Public availability at publication does not establish that a pinned tool still installs, that its weights and training data remain available, or that two tools produce scores for the same rows. NeoRepro therefore separates a broad public-artifact reproducibility profile from a narrower common-input scoring benchmark.

## Evidence map

Machine-readable study comparisons are in `research/related_work_matrix.csv`. Predictor and pipeline metadata are in `research/predictor_landscape.csv`. Detailed source excerpts are not copied into this repository; stable identifiers and source URLs are retained so each claim can be rechecked.

## Search coverage to date

Queries covered neoantigen/neoepitope prediction, prioritization, benchmarking, reproducibility, patient-level ranking, cross-study evaluation, Top-K metrics, HLA bias, leakage and recent 2025–2026 reviews and preprints. Sources included PubMed/Europe PMC, publisher pages, arXiv/medRxiv, official GitHub repositories, Zenodo and project documentation.

This review remains living: candidate papers and tools with unverified metadata are explicitly marked unknown or pending rather than silently excluded.
