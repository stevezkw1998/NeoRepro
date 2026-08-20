# Independent reviewer comments

Date: 2026-08-20

Two independent reviews were obtained after the first complete manuscript build. Reviewer A focused on leakage, statistics, split validity and reproducibility; Reviewer B focused on assays, HLA assumptions, biological interpretation and clinical claims. The comments below preserve every decision-relevant criticism in condensed form.

## Reviewer A — computational biology and statistics

### Submission-blocking comments

1. The frozen leakage protocol named mutation, patient, study and near-sequence overlap, but the first implementation checked only exact peptide and peptide–HLA overlap. A read-only check found 18 filtered records with a same-HLA, same-length PRIME2 training peptide at Hamming distance one. Each dimension must be versioned as checked or unavailable, and near-overlap requires a formal sensitivity analysis.
2. A clean-reproduction claim is premature while the worktree is uncommitted, the manifest points to an older commit, required review artifacts are absent and the manifest omits important inputs and outputs. A clean-checkout receipt is required.

### Major comments

3. The first HLA-only baseline used smoothed allele prevalence, whereas peptide baselines used class-weighted logistic regression; feature-only conclusions therefore mixed estimator and feature changes. Use the same estimator for all feature sets.
4. Top-K metrics used hashed record identifiers to break score ties. HLA-only predictions contained extensive ties, making the result depend on a biologically meaningless order. Use expectation over ties or a documented random-tie distribution.
5. Bootstrap intervals for out-of-fold baselines did not refit models, and patient bootstrap cannot estimate a population-of-studies uncertainty from three LOSO domains. Label the intervals conditional on frozen out-of-fold predictions and treat LOSO study results descriptively, or implement refitting.
6. The HLA variance fraction is score-scale-specific and the row-wise within-HLA permutation does not preserve patient/study clusters. Do not infer an isolated allele effect or biological significance from these outputs.
7. BigMHC's public immunogenicity training construction uses 9–10mers, while the benchmark contains 8mers and 11mers. Add a 9–10mer sensitivity analysis.
8. Declare one primary estimand/comparison; treat the remaining HLA, cohort and Top-K endpoints as exploratory.
9. Freeze the MHCflurry model artifact, record full-run commands/runtime/platform/hashes, and derive manifest metadata from artifacts instead of hard-coding it.

### Minor comments

- Add a random-ranking Recall@K reference.
- Avoid calibration claims for arbitrary or class-weighted scores.
- Acknowledge shared peptide–HLA records across patients.
- Ensure the manuscript auditor does not flag a negated overclaim as an overclaim.

Reviewer A independently recomputed all nine pooled AUROC/AP pairs with scikit-learn and found maximum absolute error below 1.2e-16. No pooled-metric or common-support calculation error was found.

## Reviewer B — cancer immunology and assay interpretation

### Submission-blocking comments

1. The primary Top-K unit was a patient–peptide–HLA record, while parts of the manuscript implied unique vaccine-peptide selection. Either use pMHC-pair language consistently or add a patient–peptide analysis with a declared cross-HLA aggregation rule.
2. The observed endpoint is DNA-barcoded pMHC multimer-detectable patient-matched T-cell recognition, not intrinsic immunogenicity. It does not establish natural processing, tumor-surface presentation, effector function, killing or clinical benefit. The operational schema field must not determine the biological wording.

### Major comments

3. MHCflurry had no presentation ground truth and was run without flanking context; keep it outside the main immunogenicity comparison and describe the invocation precisely.
4. IMPROVE candidates were already selected using MuPeXI, RNA evidence and NetMHCpan RankEL. The analysis is reranking after a presentation-oriented gate, not end-to-end discovery from all tumor variants.
5. Identical peptide–HLA pairs had conflicting labels across patients, proving that the endpoint depends on immune context absent from peptide/HLA-only inputs.
6. The three cohorts confound cancer, treatment, sample source, candidate generation, HLA composition and assay context. LOSO cannot isolate those factors or serve as three independent biological validations.
7. Rewrite “allele-dependent” as an unadjusted between-HLA score-variance observation; per-HLA outputs need minimum support and patient/study counts.
8. State prominently that ranking summaries condition on 60 positive-bearing patients, not all 70.
9. BigMHC and PRIME occupy the same broad score category but do not have identical biological labels or score contracts.
10. The evaluated adapters omit wild-type counterpart, expression, clonality and direct presentation evidence and therefore do not assess complete neoantigen quality.

### Minor comments

- Treat Brier values as descriptive squared error, not calibration.
- Use “publicly released pseudonymized records” rather than assuming de-identification language.
- The manuscript's clinical restraint was otherwise acceptable.
