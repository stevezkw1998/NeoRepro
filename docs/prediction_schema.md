# Standard prediction artifact

Every adapter writes one CSV row for every canonical benchmark `record_id`, including failures. The required columns are:

| Column | Meaning |
|---|---|
| `record_id` | Exact key from `data/processed/benchmark.csv` |
| `predictor` / `predictor_version` | Pinned public artifact identity |
| `task` | Scientific quantity claimed by the upstream model, such as `presentation` or `immunogenicity` |
| `score` | Adapter-selected primary raw score; never silently imputed |
| `score_direction` | `higher` or `lower` for better prioritization |
| `status` | `predicted` or a declared missing/failure reason |

Adapters may append named upstream outputs. Evaluation must preserve task labels, count all non-`predicted` rows as missing, and report both all-tool and pairwise common-support results. A failed row is never assigned a worst score in the primary analysis.
