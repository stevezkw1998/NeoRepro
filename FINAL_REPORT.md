# NeoRepro final research report

Date: 2026-08-20

## Outcome

NeoRepro delivers a leakage-aware, patient-grouped reproduction of three public MHC-I predictors on the public IMPROVE T-cell recognition screen. Its most important contribution is not a new predictor; it is a defensible evaluation result showing how training overlap, decision-unit choice and candidate preselection change what can legitimately be claimed from public neoantigen benchmarks.

The initial 520-record TESLA pilot is retained only as a positive-control fixture because every record exactly overlaps the official PRIME2 training supplement. The primary benchmark is therefore the IMPROVE screen after excluding the common union of 45 exact PRIME2 or BigMHC construction overlaps: 17,475 pMHC records, 465 positives, 70 patients and three cohorts.

## Main quantitative finding

The final post-review reporting primary is pooled AUROC on common support; it was not preregistered as primary. PRIME scored 0.597 versus 0.546 for BigMHC, a paired difference of 0.051 with a patient-bootstrap 95% interval of 0.008 to 0.092. Mean patient-pMHC Recall@20 was 0.260 for PRIME and 0.146 for BigMHC, conditional on the 60 patients with at least one positive record. MHCflurry scored AUROC 0.537 and Recall@20 0.202, but is reported as a presentation-score association analysis rather than a like-for-like immunogenicity comparison.

The result is directional rather than a claim of strong absolute prediction. Average precision was low (0.032–0.040), performance varied across patients and cohorts, and the source candidates had already passed a MuPeXI/RNA/NetMHCpan-oriented selection gate. The endpoint is DNA-barcoded pMHC multimer-detectable, patient-matched T-cell recognition—not natural processing, tumor presentation, functional killing or clinical benefit.

## Robustness and interpretation

- Excluding 35 peptides seen in PRIME2 training only under another HLA left the main direction unchanged (BigMHC AUROC 0.545; PRIME 0.596). Excluding 18 additional same-HLA, same-length Hamming-distance-one records did likewise (0.546; 0.596).
- Restricting to 9–10mer peptides left BigMHC at 0.547 and PRIME at 0.605.
- Aggregating to 15,508 patient–peptide candidates produced Recall@20 of 0.166, 0.220 and 0.304 for BigMHC, MHCflurry and PRIME, respectively. Because raw score scales vary by HLA, this analysis is exploratory; within-HLA percentile normalization before aggregation gave 0.202, 0.215 and 0.240 and preserved the ordering.
- With identical class-weighted logistic-regression estimators, peptide features outperformed HLA identity alone in both leave-one-patient-out and leave-one-study-out analyses. These are diagnostic baselines, not new deployable predictors.
- HLA-stratified quantities remain exploratory: sparse positive counts, score-scale dependence and cohort confounding prevent an isolated biological allele-effect interpretation.

## Reproducibility evidence

The repository contains pinned source revisions, adapters, standardized prediction files, analytic score-tie handling, patient bootstrap intervals, leakage and near-overlap audits, sensitivity subsets, figures, tables and a generated manuscript. Metric recomputation against scikit-learn agrees to at most 1.2e-16. A 58-file, 206,810,982-byte MHCflurry model tree is captured by SHA-256, and the unified full-predictor runner records commands, runtimes, execution/reuse status, platform details and output hashes. Existing predictions are reused only after exact row-order, record-ID, model-revision, status and score validation.

Run `make -j4 reproduce-results` to regenerate analyses, figures, tables and the manuscript from the versioned benchmark and prediction files while parallelizing independent bootstrap analyses. Omit `-j4` on a constrained machine. Run `make -j4 full-reproduce` to also acquire the pinned public inputs and install and execute the licensed third-party predictors. The latter requires explicit acceptance of BigMHC and PRIME academic-use terms.

## Independent review

One statistical/reproducibility review and one biological/endpoint review were completed independently. Their comments and point-by-point dispositions are preserved in `paper/reviewer_comments.md` and `paper/reviewer_response.md`. The review resulted in near-overlap and peptide-unit sensitivities, matched-estimator baselines, analytic Top-K tie handling, narrower endpoint language and explicit limits on HLA interpretation.

## Remaining submission-only tasks

The scientific and computational work is complete. Before external submission, a human owner must supply author names, affiliations and ORCIDs; funding and conflict-of-interest statements; a real repository/archive URL and DOI; venue-specific formatting; and confirmation of any ethics language required when describing the already-published source cohort. A fresh literature check should also be run immediately before submission.
