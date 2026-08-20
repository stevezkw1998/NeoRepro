# NeoRepro research specification

Version: 0.2.0 (2026-08-20; post-novelty audit)

## Objective

Measure how reproducible, comparable, and useful for patient-level prioritization publicly accessible neoantigen prediction tools remain under a standardized, leakage-aware evaluation.

The literature audit required a narrower dual-track design. Any further scope change must preserve a dated reason in `research/research_log.md`.

## Study tracks

- Track A profiles the public-artifact reproducibility of a broad, heterogeneous set of citable tools. Installation and runtime outcomes are results even when tools are not scientifically comparable.
- Track B reruns a smaller set of locally executable MHC-I peptide–HLA scorers on identical experimentally tested records. Binding, presentation and immunogenicity scores remain labeled as different tasks and are not collapsed into one overall winner.

## Primary questions

1. What fraction of eligible public predictors can be installed and run from their public artifacts under a documented low-cost protocol?
2. Do comparative rankings change between pooled discrimination and patient-level Top-K prioritization?
3. How stable are fixed-tool results across patients and source studies, and how do transparent NeoRepro baselines change under patient-held-out and study-held-out fitting when source data support those designs?
4. How sensitive are results to known training overlap, HLA composition, study source, assay, and missing predictions?

## Units and estimands

- Reproducibility unit: a pinned predictor release or repository revision.
- Prediction unit: an experimentally annotated peptide–HLA observation.
- Principal comparison unit: patient, with study as the principal external-generalization grouping.
- Principal prioritization estimands: Recall@K, HitRate@K, MRR, and NDCG@K for declared K values.
- Supporting estimands: AUROC, average precision, calibration/Brier score, and failure/missingness rates.

Patient-level Top-K evaluation and HLA shortcut bias are established prior work, not novelty claims. NeoRepro's contribution is the reproducibility profile, standardized rerun, common-support analysis, and pooled-versus-patient metric concordance.

## Predictor eligibility

A candidate must have a citable method, public access route, a sufficiently specified inference contract, and legal eligibility for academic evaluation. Code availability, local installability, server availability, and benchmark inclusion are recorded separately. Failed reproduction remains an outcome.

## Dataset eligibility

Include only records with traceable source provenance and a defensible experimental label. Patient-held-out analyses require source-grounded patient identifiers. Study-held-out analyses require source-grounded study identifiers. Untested candidates are not negatives. Restricted source data are fetched by documented scripts and are not redistributed.

## Leakage policy

Audit exact peptide, peptide–HLA, mutation, patient, study, near-sequence, and known predictor-training overlap separately. Mark unavailable training overlap as unknown. Fit learned preprocessing and calibration only inside training folds.

## Pilot gate

The cheap pilot uses MHCflurry 2.0, BigMHC-IM, and PRIME 2.0 when license/platform checks permit, plus a small provenance-complete TESLA subset. Scale only if:

- the research gap survives current-literature review;
- canonical schema and provenance checks pass;
- at least two predictors yield comparable scores or rankings;
- score direction and missing-output semantics are verified;
- pooled and patient-level metric fixtures pass;
- runtime and projected spend remain compatible with the budget.

## Cost and claim constraints

Prefer CPU, Apple Silicon, public data, precomputed outputs when scientifically valid, and isolated environments. Target additional spend below USD 50. Computational results may support claims about reproducibility or prioritization assessment, not clinical benefit.

## Completion criteria

Deliver a GitHub-ready repository, predictor registry, provenance-preserving benchmark, reproducible adapters, versioned raw predictions, statistical results and figures, a complete English manuscript/preprint, reviewer records, and an exact clean-checkout reproduction command.
