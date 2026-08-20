# NeoRepro extension: independent value audit

Date: 2026-08-20  
Scope: generic scientific/readiness audit; no target venue was specified.

## Verdict

**Near-ready as a reproducibility/benchmarking resource; borderline as a general-purpose prediction-method paper.** The extension raises the work from a useful but single-dataset comparison to a medium-strength substantive contribution. It still does not create a new predictor or establish clinical utility.

## What is genuinely new and valuable

1. **A pre-frozen independent-domain result changes the scientific conclusion.** In IMPROVE, PRIME exceeded BigMHC; in the Zhao vaccine cohort, BigMHC exceeded PRIME by 0.057 patient-macro NDCG@5 (paired patient-bootstrap 95% CI 0.008–0.106). This is direct evidence that model ordering is domain-dependent, not a repetition of the original conclusion.
2. **The same-task model set is materially broader.** DeepImmuno-CNN and DeepHLApan were reproduced from pinned public weights, bringing the external comparison to four immunogenicity models plus a task-distinct presentation control. The work also preserves unsupported coverage rather than applying fuzzy HLA substitution.
3. **The data gate produced a real negative result.** A 2.36-GB NCI candidate archive was rejected before inference because untested short candidates could not be relabelled as experimental negatives. This prevents a superficially larger but invalid benchmark and is a reusable methodological contribution.
4. **The external data are traceable and almost entirely free of known exact overlap.** The canonical dataset contains 2,317 individually administered peptides from 352 patients; only two known exact training overlaps were removed. The source workbook member, transformation, row provenance and overlap classifications are checksum-pinned.

## Evidence strength

- Strong: endpoint and primary NDCG@5 frozen before external inference; patient is the uncertainty unit; 2,000 paired bootstrap replicates; analytic tie handling; pairwise common support; exact-overlap union exclusion; all quantitative manuscript values generated from results.
- Moderate: Zhao tests vaccine-elicited post-vaccination ELISPOT, not the same multimer endpoint as IMPROVE. It is complementary domain validation, not a pure biological replication.
- Weak/unknown: DeepHLApan has no official row-level training manifest; DeepImmuno-CNN covers 43.8% of Zhao; source patient/study overlap with historical model training cannot be fully audited; only one external study supplies the vaccine endpoint.
- Absolute predictive evidence remains modest: pooled AUROC is 0.488–0.550 across full/near-full-support immunogenicity models on Zhao. High NDCG@5 values partly reflect a median of only six candidates per patient.

## Generic readiness rubric

| Dimension | Score | Reason |
|---|---:|---|
| Contribution focus | 13/15 | Clear leakage-aware reproducibility and domain-robustness contribution; not a new model. |
| Significance | 12/15 | Addresses a consequential benchmarking failure mode and patient ranking. |
| Novelty/positioning | 11/15 | Domain reversal and reproducibility evidence are useful; benchmarking concepts themselves are not wholly new. |
| Methodological validity | 18/20 | Frozen external protocol, correct grouping, common support and disciplined endpoints; one training manifest remains unavailable. |
| Experimental evidence | 16/20 | Two patient datasets and four same-task models externally; endpoints differ and one model has limited coverage. |
| Clarity/claim discipline | 9/10 | Claims explicitly stop short of natural presentation and clinical efficacy. |
| Reproducibility/ethics/limitations | 5/5 | Pinned sources, checksums, adapters, tests, manifests and endpoint limitations are explicit. |
| **Total** | **84/100** | **Near-ready generically; venue fit unresolved.** |

## Decisive limitations

1. This is strongest as a benchmarking/resource paper, not as an algorithmic-method advance.
2. The independent cohort changes both population/intervention and assay, so it establishes domain sensitivity rather than same-endpoint replication.
3. DeepHLApan leakage cannot be ruled out beyond available public evidence.
4. Model rankings should not be converted into a universal winner or clinical recommendation.

## Bottom line

The extension adds real scientific value. Its strongest defensible claim is: **public peptide–HLA immunogenicity model ordering reverses across two patient-level evaluation domains even after known exact-overlap control, so claims of universal superiority from a single neoantigen benchmark are not stable.** That is publishable resource/methodology evidence if positioned narrowly. The contribution would be overstated if sold as a new predictor, a same-endpoint external replication, or evidence of vaccine efficacy.
