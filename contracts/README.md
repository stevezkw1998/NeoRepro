# NeoRepro plug-in contract

## Standard one-file entry point

The fastest public interface accepts one UTF-8 CSV and writes both a machine-readable
`evaluation.json` and a human-readable `report.md`:

```bash
python -m pip install .
neorepro benchmark predictions.csv --output-dir neorepro-results
```

Required columns:

```text
record_id,patient_id,study_id,label,score,predictor
```

Each record's truth metadata must be identical across predictors. `label` is `0` or `1`, and
larger scores are better unless `score_direction` declares `lower`. Blank scores are counted as
unsupported. Optional columns are `score_direction`, `status`, `training_overlap`, `hla`, `assay`
and `cancer_type`. `training_overlap` accepts `exact`, `none` or `unknown`; exact overlaps are
excluded from the primary common-support comparison, while unknown remains unknown.

The command reports AUROC, AUPRC, fixed-threshold classification metrics, eligible Brier score,
tie-aware patient Recall/Precision/HitRate/NDCG at K=5/10/20, MRR, patient bootstrap confidence
intervals, paired predictor differences, support-matched random ranking and available study/HLA/
assay/cancer-type strata. Stratified views are descriptive, not held-out validation.

See `contracts/synthetic/standard_predictions.csv` for a complete two-predictor example.

## Card and separate-artifact interface

Third parties can also validate cards and separate artifacts before evaluation:

```bash
neorepro dataset validate contracts/dataset-card.example.json
neorepro predictor validate contracts/predictor-card.example.json
neorepro artifact predictions.csv --benchmark benchmark.csv
neorepro evaluate benchmark.csv predictions.csv --output results/evaluation.json --report reports/evaluation.md
neorepro overlap-audit predictions.csv
```

Every artifact must contain one row for every benchmark `record_id`. Failed or unsupported predictions remain explicit rows and are counted as missing; they are never imputed. `score_direction` is mandatory and evaluation orients lower-is-better scores before metrics. Unknown training overlap is reported as unknown, not as independence.
