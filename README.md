[English](README.md) | [简体中文](README.zh-CN.md) | [繁體中文](README.zh-TW.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | [Deutsch](README.de.md) | [Español](README.es.md) | [Français](README.fr.md)

# NeoRepro

> 🧪 **[We are actively seeking external reviewers and predictor authors.](https://github.com/stevezkw1998/NeoRepro/issues/2)**
>
> 15–30 min sanity checks, reproduction attempts, dataset suggestions and adversarial critiques are welcome.

NeoRepro is a leakage-aware, patient-level, reproducible benchmark resource for public MHC-I peptide–HLA neoantigen predictors. It packages pinned predictor artifacts, record-level provenance, training-overlap audits, common-support comparisons, patient-level uncertainty, support-matched random baselines and machine-generated results.

This is a benchmark/resource contribution, not a new predictor and not a claim of a universal model winner or clinical utility.

## Start here

- **Current manuscript:** [resource-positioned manuscript](paper/manuscript_resource.md).
- **Two-minute evidence summary:** [bilingual expert brief](output/pdf/neorepro_expert_brief_bilingual.pdf) and [independent-cohort extension summary](reports/extension_summary.md).
- **Reproduce the frozen results:** use the command in the Reproduce section below.
- **Cite a fixed version:** [CITATION.cff](CITATION.cff) and the [v0.1.0 release](https://github.com/stevezkw1998/NeoRepro/releases/tag/v0.1.0).

For the scientific contract and scope, see [RESEARCH_SPEC.md](RESEARCH_SPEC.md).

## Status

- Current-literature audit: complete; decision `RESCOPE, then GO`
- Reproduced predictors: MHCflurry 2.2.1, BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN and DeepHLApan
- TESLA pilot: complete; reclassified as a training-overlap-positive control
- Primary benchmark: IMPROVE, 17,475 leakage-filtered rows, 70 patients, 3 cohorts
- Primary IMPROVE inference: complete; 52,425 fixed-tool predictions with no missing rows
- Manuscript: [resource-positioned version](paper/manuscript_resource.md), generated from frozen result files; independent statistical and biological review complete

## Main result

The official PRIME2 supplement showed that all 520 records in the initial TESLA fixture were exact training overlaps, so they are retained only as a leakage-positive control. On the common exact-overlap-filtered, presentation-prefiltered IMPROVE benchmark, PRIME achieved AUROC 0.597 and mean patient-pMHC Recall@20 0.260; BigMHC achieved 0.546 and 0.146. In the independent Zhao vaccine cohort, BigMHC patient NDCG@5 was 0.658 versus a support-matched random reference of 0.578; DeepHLApan was 0.580 versus 0.578, while DeepImmuno-CNN was 0.755 versus 0.759 on 43.8% coverage. These results support an auditable, task- and support-aware evaluation contract, not a universal leaderboard.

## Reproduce

Install [uv](https://docs.astral.sh/uv/), then rebuild every analysis, figure, table and manuscript artifact with the project-pinned CPython 3.11.15 from the versioned benchmark and prediction files:

```bash
make -j4 reproduce-results
```

Independent bootstrap analyses are parallelized by Make. Use `make reproduce-results` without `-j4` when CPU or memory is constrained. `make -j4 full-reproduce` additionally downloads the pinned public source data and installs/runs the third-party predictors. It requires explicit acceptance of the academic-only BigMHC and PRIME terms, several gigabytes of disk space, and substantially more runtime.

## Evidence trail

- **Primary scientific record:** [current manuscript](paper/manuscript_resource.md), [final report](FINAL_REPORT.md), and [review record](paper/reviewer_response.md).
- **Auditable outputs:** [final result table](results/final_results.csv), [figures](results/figures/), [training-overlap audit](research/training_overlap_summary_improve.json), and [SHA-256 manifest](results/manifest.json).
- **Submission planning:** [target-venue strategy](reports/target_venues_2026-08-20.md).

The independent Zhao 2026 vaccine-cohort extension is reproduced with `make -j4 extension`. Its concise evidence summary is in [reports/extension_summary.md](reports/extension_summary.md), with the frozen pre-inference contract in [research/extension_protocol.json](research/extension_protocol.json). The external endpoint is post-vaccination ELISPOT after peptide-pulsed dendritic-cell administration and must not be interpreted as natural tumor presentation or clinical efficacy.

## License

Original NeoRepro code and documentation use the MIT License. Third-party predictors and datasets retain their own terms; inclusion in the study does not imply redistribution permission.
