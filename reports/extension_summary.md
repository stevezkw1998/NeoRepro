# Independent-cohort extension summary

Zhao 2026 contributed 2,317 individually administered 8–11mer peptides from 352 patients. After removing 2 known exact training overlaps, 2,315 records, 311 positives, and 131 positive-bearing patients remained.

The endpoint is post-vaccination IFN-γ ELISPOT after peptide-pulsed dendritic-cell administration. It is a valid independent ranking test for this intervention context, but not evidence of natural tumor presentation, untreated intrinsic immunogenicity, tumor killing, or clinical benefit.

## Frozen primary result

| Predictor | Coverage | AUROC | AP | NDCG@5 (95% patient-bootstrap CI) | Recall@5 |
|---|---:|---:|---:|---:|---:|
| DeepImmuno-CNN | 43.8% | 0.526 | 0.158 | 0.755 (0.691–0.816) | 0.925 |
| BigMHC | 100.0% | 0.550 | 0.148 | 0.658 (0.606–0.707) | 0.816 |
| PRIME | 99.8% | 0.531 | 0.148 | 0.604 (0.546–0.660) | 0.770 |
| DeepHLApan | 100.0% | 0.488 | 0.131 | 0.580 (0.524–0.635) | 0.726 |

On near-complete common support, BigMHC exceeded PRIME by 0.057 NDCG@5 (95% CI 0.008–0.106) and DeepHLApan by 0.078 (0.022–0.133). DeepImmuno-CNN's apparently larger marginal value is not a full-cohort win: it covered 43.8%, and its common-support differences from the other models were unresolved.
NDCG@5 is numerically high because the median patient had only six administered candidates; this is why cross-dataset NDCG magnitudes should not be compared directly.
DeepHLApan training-set identity remains unknown because no official row-level manifest is public.

## Cross-dataset check

- BigMHC: IMPROVE→Zhao AUROC 0.546→0.550; NDCG@5 0.060→0.658.
- PRIME: IMPROVE→Zhao AUROC 0.597→0.531; NDCG@5 0.099→0.604.

## Expanded IMPROVE 9–10mer model set

- PRIME: n=15,234, AUROC 0.605, patient NDCG@5 0.102.
- BigMHC: n=15,234, AUROC 0.547, patient NDCG@5 0.070.
- DeepImmuno-CNN: n=11,036, AUROC 0.527, patient NDCG@5 0.021.
- DeepHLApan: n=15,234, AUROC 0.508, patient NDCG@5 0.023.
