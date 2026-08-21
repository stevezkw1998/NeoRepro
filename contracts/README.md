# NeoRepro plug-in contract

Third parties can validate cards and artifacts, then evaluate in one command:

```bash
neorepro dataset validate contracts/dataset-card.example.json
neorepro predictor validate contracts/predictor-card.example.json
neorepro artifact predictions.csv --benchmark benchmark.csv
neorepro evaluate benchmark.csv predictions.csv --output results/evaluation.json --report reports/evaluation.md
neorepro overlap-audit predictions.csv
```

Every artifact must contain one row for every benchmark `record_id`. Failed or unsupported predictions remain explicit rows and are counted as missing; they are never imputed. `score_direction` is mandatory and evaluation orients lower-is-better scores before metrics. Unknown training overlap is reported as unknown, not as independence.
