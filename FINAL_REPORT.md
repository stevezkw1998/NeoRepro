# NeoRepro final research report

Date: 2026-08-20

## Outcome

NeoRepro delivers a leakage-aware, patient-grouped reproduction of five public MHC-I predictors across the IMPROVE T-cell recognition screen and an independent personalized-vaccine cohort. Its most important contribution is not a new predictor; it is a defensible evaluation result showing how training overlap, decision unit, endpoint and candidate preselection change what can legitimately be claimed from public neoantigen benchmarks.

The initial 520-record TESLA pilot is retained only as a positive-control fixture because every record exactly overlaps the official PRIME2 training supplement. The primary benchmark is therefore the IMPROVE screen after excluding the common union of 45 exact PRIME2 or BigMHC construction overlaps: 17,475 pMHC records, 465 positives, 70 patients and three cohorts.

## Main quantitative finding

The final post-review reporting primary is pooled AUROC on common support; it was not preregistered as primary. PRIME scored 0.597 versus 0.546 for BigMHC, a paired difference of 0.051 with a patient-bootstrap 95% interval of 0.008 to 0.092. Mean patient-pMHC Recall@20 was 0.260 for PRIME and 0.146 for BigMHC, conditional on the 60 patients with at least one positive record. MHCflurry scored AUROC 0.537 and Recall@20 0.202, but is reported as a presentation-score association analysis rather than a like-for-like immunogenicity comparison.

The result is directional rather than a claim of strong absolute prediction. Average precision was low (0.032–0.040), performance varied across patients and cohorts, and the source candidates had already passed a MuPeXI/RNA/NetMHCpan-oriented selection gate. The endpoint is DNA-barcoded pMHC multimer-detectable, patient-matched T-cell recognition—not natural processing, tumor presentation, functional killing or clinical benefit.

## Independent-cohort extension

The frozen extension added the Zhao 2026 cohort: 2,317 individually administered 8–11mer peptides from 352 patients, all assayed after vaccination by IFN-γ ELISPOT. Removing two known exact training overlaps left 2,315 records, 311 positives and 131 positive-bearing patients. The primary metric, patient-macro NDCG@5, was frozen before inference because the median patient had only six administered candidates.

On near-complete common support, BigMHC exceeded PRIME by 0.057 NDCG@5 (patient-bootstrap 95% CI 0.008–0.106) and DeepHLApan by 0.078 (0.022–0.133). This reverses the BigMHC–PRIME direction observed in IMPROVE and is the extension's strongest scientific result: current model ordering is domain-dependent rather than universal. DeepImmuno-CNN covered only 43.8% of the cohort; its common-support differences from the other immunogenicity models were unresolved. DeepHLApan's row-level training identity remains unknown because its official repository exposes no training manifest.

This cohort is complementary, not a pure biological replication. Peptide-pulsed dendritic-cell administration can induce or amplify post-vaccination responses, so these results do not establish natural tumor presentation, untreated intrinsic immunogenicity, tumor killing or clinical benefit.

On the original IMPROVE 9–10mer subset, the expanded model set retained the original direction: PRIME AUROC 0.605, BigMHC 0.547, DeepImmuno-CNN 0.527 on its 11,036 supported records, and DeepHLApan 0.508. Thus the external reversal is not explained merely by adding the two older models; it is specifically a dataset/endpoint-domain change.

## Robustness and interpretation

- Excluding 35 peptides seen in PRIME2 training only under another HLA left the main direction unchanged (BigMHC AUROC 0.545; PRIME 0.596). Excluding 18 additional same-HLA, same-length Hamming-distance-one records did likewise (0.546; 0.596).
- Restricting to 9–10mer peptides left BigMHC at 0.547 and PRIME at 0.605.
- Aggregating to 15,508 patient–peptide candidates produced Recall@20 of 0.166, 0.220 and 0.304 for BigMHC, MHCflurry and PRIME, respectively. Because raw score scales vary by HLA, this analysis is exploratory; within-HLA percentile normalization before aggregation gave 0.202, 0.215 and 0.240 and preserved the ordering.
- With identical class-weighted logistic-regression estimators, peptide features outperformed HLA identity alone in both leave-one-patient-out and leave-one-study-out analyses. These are diagnostic baselines, not new deployable predictors.
- HLA-stratified quantities remain exploratory: sparse positive counts, score-scale dependence and cohort confounding prevent an isolated biological allele-effect interpretation.

## Reproducibility evidence

The repository contains a CPython 3.11.15 pin, pinned source revisions, adapters, standardized prediction files, analytic score-tie handling, patient bootstrap intervals, leakage and near-overlap audits, sensitivity subsets, figures, tables and a generated manuscript. Metric recomputation against scikit-learn agrees to at most 1.2e-16. A 58-file, 206,810,982-byte MHCflurry model tree is captured by SHA-256, and the unified full-predictor runner records commands, runtimes, execution/reuse status, platform details and output hashes. Existing predictions are reused only after exact row-order, record-ID, model-revision, status and score validation.

The documented command was also executed from a clean clone of commit `f4d86e6fbffb8062952eab3ec0d6d236a936a67d` using CPython 3.11.15. It completed in 734 seconds with Ruff passing, 27/27 tests passing and all tracked generated artifacts byte-identical; only the manifest's expected source-commit and clean-state metadata changed. The machine-readable receipt is `reports/clean_reproduction.json`.

The completed extension was independently checked from a fresh clone of commit `9373c0ab3ef4aa381839f8e23b084f2818aaaaac` in a fresh uv environment: Ruff passed and all 32/32 tests passed. The receipt is `reports/extension_clean_reproduction.json`.

Run `make -j4 reproduce-results` to regenerate analyses, figures, tables and the manuscript from the versioned benchmark and prediction files while parallelizing independent bootstrap analyses. Omit `-j4` on a constrained machine. Run `make -j4 full-reproduce` to also acquire the pinned public inputs and install and execute the licensed third-party predictors. The latter requires explicit acceptance of BigMHC and PRIME academic-use terms.

## Independent review

One statistical/reproducibility review and one biological/endpoint review were completed independently for the original analysis. Their comments and point-by-point dispositions are preserved in `paper/reviewer_comments.md` and `paper/reviewer_response.md`. The extension received a separate rubric-based value and evidence audit in `reports/extension_value_audit.md`; it is not misrepresented as a second blinded peer review.

## Remaining submission-only tasks

The scientific and computational work is complete. Author identity, affiliation and ORCID metadata are now supplied. Before external submission, a human owner must supply funding and conflict-of-interest statements; a real repository/archive URL and DOI; venue-specific formatting; and confirmation of any ethics language required when describing the already-published source cohort. A fresh literature check should also be run immediately before submission.
