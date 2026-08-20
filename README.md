# NeoRepro

NeoRepro is an evidence-first study of the reproducibility and patient-level evaluation of public neoantigen prediction tools.

See [RESEARCH_SPEC.md](RESEARCH_SPEC.md) for the scientific contract and [PROJECT_PROMPT.md](PROJECT_PROMPT.md) for the original project brief.

## Status

- Repository initialized: yes
- Current-literature audit: complete; decision `RESCOPE, then GO`
- Reproduced predictors: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0
- TESLA pilot: complete; reclassified as a training-overlap-positive control
- Primary benchmark: IMPROVE, 17,475 leakage-filtered rows, 70 patients, 3 cohorts
- Full inference and analysis: complete; 52,425 fixed-tool predictions with no missing rows
- Manuscript: generated from frozen result files; independent statistical and biological review complete

## Main result

The official PRIME2 supplement showed that all 520 records in the initial TESLA fixture were exact training overlaps, so they are not used as external performance evidence. On the common exact-overlap-filtered, presentation-prefiltered IMPROVE benchmark, PRIME achieved AUROC 0.597 and mean patient-pMHC Recall@20 0.260; BigMHC achieved 0.546 and 0.146. Recall conditions on the 60 patients with at least one detected positive. Absolute performance remained modest and heterogeneous across patients. Near-overlap exclusion, a 9–10mer restriction and patient–peptide aggregation preserved the qualitative ordering. Transparent held-out baselines found more stable signal in peptide features than in HLA identity alone.

## Reproduce

Install [uv](https://docs.astral.sh/uv/), then rebuild every analysis, figure, table and manuscript artifact with the project-pinned CPython 3.11.15 from the versioned benchmark and prediction files:

```bash
make -j4 reproduce-results
```

Independent bootstrap analyses are parallelized by Make. Use `make reproduce-results` without `-j4` when CPU or memory is constrained. `make -j4 full-reproduce` additionally downloads the pinned public source data and installs/runs the third-party predictors. It requires explicit acceptance of the academic-only BigMHC and PRIME terms, several gigabytes of disk space, and substantially more runtime.

Key outputs are the [final report](FINAL_REPORT.md), [manuscript](paper/manuscript.md), [review record](paper/reviewer_response.md), [final result table](results/final_results.csv), [figures](results/figures/), [training-overlap audit](research/training_overlap_summary_improve.json), and [SHA-256 manifest](results/manifest.json).

## License

Original NeoRepro code and documentation use the MIT License. Third-party predictors and datasets retain their own terms; inclusion in the study does not imply redistribution permission.
