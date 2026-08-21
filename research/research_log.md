# Research log

## 2026-08-20 — Project initialization

- Decision: use the existing repository root rather than create a nested `NeoRepro/` directory.
- Reason: the working directory is already the named project and already contains an initialized Git repository.
- Decision: freeze a provisional research specification before literature discovery.
- Reason: prevent results-driven changes to questions, units, and pilot gates while allowing evidence-driven rescoping after the novelty audit.
- Environment: optional OpenAI and Anthropic API keys were not present; this is not blocking because literature and code sources can be verified directly.

## 2026-08-20 — Novelty audit and rescope

- Evidence: TESLA already established patient-specific ranking and Top-20 evaluation; ITSNdb and NeoHunter extended comparative prioritization; 2026 work directly addresses HLA shortcut bias and Top-20 ranking.
- Removed novelty claims: first patient-level Top-K neoantigen benchmark; first HLA-bias analysis.
- Final design: separate a broad public-artifact reproducibility profile from a smaller common-input MHC-I peptide–HLA scoring benchmark.
- Primary novelty: pinned reruns, failure provenance, missing-output/common-support fairness, and concordance between pooled and patient-level conclusions.
- Pilot decision: start with MHCflurry 2.0, BigMHC-IM, and PRIME 2.0 subject to exact license/platform checks, using patient-grouped TESLA records.

## 2026-08-20 — Local build-path failure

- Failed approach: `setuptools.build_meta` editable install under the repository path containing Unicode em dash (`—`).
- Evidence: editable-wheel creation raised `UnicodeEncodeError` while encoding the generated `.pth` path as ASCII.
- Resolution: switched the project build backend to Hatchling. Wheel creation succeeded, but editable installs still failed when a generated `.pth` file containing the Unicode path was decoded as ASCII. Project install and CI commands therefore use a regular wheel; source-tree tests may use `PYTHONPATH=src`.

## 2026-08-20 — Pilot data freeze and predictor licensing

- Frozen pilot: DeepImmuno's commit-pinned transformed TESLA table, 522 source rows and 520 unique patient-peptide-HLA observations after removing two byte-identical source duplicates.
- Audit: 35 positive observations across six patient identifiers and one study. Patient-level ranking is supported; study-held-out claims are not supported by this pilot.
- Predictor freeze: MHCflurry 2.2.1, BigMHC v1.0, and PRIME 2.0 plus MixMHCpred 2.2.
- License decision: MHCflurry is redistributable under Apache-2.0. BigMHC is academic-only with conditional redistribution. PRIME and MixMHCpred are academic-only and non-transferable, so their upstream artifacts must not be committed or repackaged.

## 2026-08-20 — Three-predictor reproduction gate

- MHCflurry 2.2.1: 520/520 records predicted on CPU; two full outputs were byte-identical. A custom downloads directory breaks release lookup in the upstream CLI, so the reproducible command uses `MHCFLURRY_DATA_DIR` plus `MHCFLURRY_DOWNLOADS_CURRENT_RELEASE=2.2.0`.
- BigMHC v1.0: 520/520 records predicted on CPU with the paper dependency versions. The distributed EL fixture agreed within `2.6e-7`. The adapter rejects unsupported HLA alleles before BigMHC's silent fuzzy substitution can occur.
- PRIME 2.0 with MixMHCpred 2.2: distributed macOS binaries were x86-64, so both provided C++ sources were compiled locally for ARM64. The adapter stages the programs under a space-free temporary path and forces the `C` locale for macOS Perl. The 146-row distributed fixture matched exactly and 520/520 pilot records were predicted.
- Gate decision: pass. All three pinned tools produced complete scores on the identical pilot rows within the CPU/budget constraints; proceed to standardized evaluation while preserving task labels.

## 2026-08-20 — Training-overlap failure and benchmark rescope

- Official source: PRIME2 Table S4 (`mmc6.xlsx`) from the Europe PMC supplementary archive, retained locally only; archive and workbook checksums are versioned.
- Decisive result: all 520 unique TESLA pilot records were exact peptide–HLA matches in PRIME2 training with concordant labels and `Random=0`. All were length 9–10 and therefore also satisfy the published BigMHC `im_trainval` construction from non-random PRIME1/2 records.
- Consequence: PRIME and BigMHC TESLA metrics are artifact-reproduction/training-overlap descriptions, not evidence of generalization or superiority. The original paired comparison is retained as an audit artifact but withdrawn from scientific interpretation.
- Replacement: IMPROVE's pinned public archive contains 17,520 patient-matched T-cell screening records, 467 positives, 70 patients, 36 HLA alleles, and three source cohorts.
- IMPROVE overlap audit: 45 records are exact PRIME2 peptide–HLA matches (43 also satisfy BigMHC's immunogenicity-training construction). Their union is excluded for all fixed tools, yielding one common set of 17,475 records and 465 positives while retaining all 70 patients and three studies.

## 2026-08-20 — Full common-support inference and evaluation

- Complete inference: MHCflurry, BigMHC and PRIME each produced 17,475/17,475 predictions on the filtered IMPROVE benchmark; the three outputs are checksum-frozen with no missing rows.
- Fixed immunogenicity comparison: PRIME versus BigMHC yielded AUROC 0.5969 versus 0.5458 and average precision 0.03964 versus 0.03186. The patient-bootstrap 95% interval for PRIME minus BigMHC AUROC was 0.0077–0.0922.
- Patient retrieval: mean Recall@20 was 0.2600 for PRIME, 0.1458 for BigMHC and 0.2021 for the task-distinct MHCflurry presentation score. Only the two immunogenicity tools receive a paired same-task comparison.
- Transparent controls: peptide-only logistic regression exceeded HLA-only regression under both patient-held-out and study-held-out fitting. Adding HLA did not resolve an improvement over peptide alone and reduced the study-held-out AUROC point estimate.
- HLA sensitivity: within-HLA ranking preserved or improved AUROC for all fixed tools; HLA mean scores alone were near chance. BigMHC nevertheless had 32.5% of its score variance explained by HLA, showing that allele dependence and label shortcut performance are distinct diagnostics.
- Metric verification: all nine fixed/baseline AUROC and average-precision pairs matched scikit-learn to less than 1e-12; 23 deterministic repository tests passed.

## 2026-08-20 — Independent review and robustness revision

- Review design: one independent statistical/reproducibility audit and one independent biological/endpoint audit were completed before finalization; all comments and dispositions are preserved under `paper/`.
- Leakage robustness: the audit now covers exact peptide, exact peptide–HLA and same-HLA/same-length Hamming-distance-one matches. Eighteen retained records, including two positives, had a distance-one PRIME2 neighbor; excluding them left BigMHC and PRIME AUROC at 0.546 and 0.596.
- Decision-unit robustness: a patient–peptide analysis aggregates any-HLA positives and the maximum oriented score. It contains 15,508 candidates and preserves the ranking direction, with Recall@20 of 0.166, 0.220 and 0.304 for BigMHC, MHCflurry and PRIME.
- Length robustness: restriction to 15,234 9–10mer records preserves the direction (BigMHC AUROC 0.547; PRIME 0.605).
- Baseline correction: HLA-only, peptide-only and HLA-plus-peptide controls now use the same class-weighted logistic-regression estimator and differ only in feature set. Top-K metrics use analytic expectations at score-tie boundaries; this particularly corrects HLA-only retrieval estimates.
- Interpretation correction: the endpoint is described as DNA-barcoded pMHC multimer-detectable patient-matched T-cell recognition within a presentation-prefiltered candidate set. It is not interpreted as intrinsic immunogenicity, natural processing, tumor presentation, killing or clinical benefit.
- HLA correction: the variance fraction is explicitly score-scale-specific, unadjusted and confounded by compound cohort domains. Per-HLA output now reports sample, positive, patient and study support, and no isolated biological allele-effect claim is made.
- Final reporting primary: pooled common-support AUROC for PRIME versus BigMHC. Average precision, patient Top-K, cohort, HLA and baseline results are supporting or exploratory.
- Reporting-hierarchy provenance: the original frozen specification emphasized patient Top-K and treated AUROC as supporting. Independent review motivated designating pooled AUROC as the final same-task reporting primary because it avoids choosing a patient-specific K; this is a transparent post-review revision, not a preregistered primary endpoint.
- Additional exact-peptide sensitivity: 35 primary-benchmark records contained a peptide seen in PRIME2 only under another HLA. Peptide specificity is HLA-conditioned, so they remain outside the primary exact peptide–HLA exclusion but receive a separate versioned exclusion analysis.
- Cross-HLA aggregation sensitivity: raw maximum-score patient–peptide aggregation is exploratory because score scales vary by HLA. A second analysis first transforms scores to empirical within-HLA mid-percentiles and then takes the maximum.

## 2026-08-20 — External extension frozen before prediction

- Motivation: the completed study remained limited to one eligible performance dataset, two fixed same-task immunogenicity predictors, and a transparently post-review primary reporting choice.
- Dataset decision: use the CC-BY-4.0 NCI Surgery Branch mutated-minimal-peptide test set (`10.35092/yhjc.11400987.v2`) as the second patient-grouped domain. Only rows with explicit experimental positive/negative screening outcomes are eligible; unscreened candidates are never converted to negatives.
- Predictor decision: attempt DeepImmuno-CNN and DeepHLApan because both expose public local peptide–HLA immunogenicity artifacts and can also be tested on the existing benchmark within their declared domains. PredIG was not selected because its required parental-protein, NOAH and NetCleave inputs are not consistently available in the current canonical datasets.
- Frozen primary: patient-macro pMHC Recall@20 on pairwise common same-task support, with paired patient bootstrap and analytic tie handling. No external predictions were generated before `research/extension_protocol.json` was written.
- Failure policy: legacy-environment failure, unsupported HLA, and unknown training overlap remain results; no model is silently replaced or evaluated outside its declared input contract.

## 2026-08-20 — NCI gate failure and external-dataset replacement

- NCI eligibility result: the 2.36-GB test file contains 2,622,623 enumerated short peptide–HLA candidates. `Screening Status` describes the parent mutation/long-peptide screen; it does not establish that every enumerated short candidate was individually tested. Treating those rows as pMHC negatives would violate the frozen data rules, so the NCI pMHC protocol failed before any prediction.
- Replacement source: Zhao et al. (`10.3389/fimmu.2026.1829509`) provide 2,317 SNV-derived 8–11mer peptides administered to 352 patients, each with a post-vaccination IFN-γ ELISPOT ratio. The source threshold of 2.0 defines 313 positive peptide responses. The article and supplementary workbook are CC-BY-4.0 and checksum-verifiable through Europe PMC.
- Metric correction before prediction: because patients received only a small number of selected peptides, Recall@20 would saturate. The replacement protocol freezes patient-macro NDCG@5 as primary, with Recall@5, MRR, pooled AUROC/AP and coverage as supporting estimands.
- Interpretation boundary: this external domain tests vaccine-elicited response after peptide-pulsed dendritic-cell administration. It is biologically complementary to IMPROVE, not a like-for-like replication of natural presentation or the multimer endpoint.
## 2026-08-20 — Independent extension completed

- Reproduced DeepImmuno-CNN at `df42ac5b` and DeepHLApan at `ac1f4beb` in isolated TensorFlow 2.15.1 environments. DeepHLApan required a semantics-preserving loader for the published legacy `GRU(reset_after=False)` weights; both adapters disable fuzzy HLA substitution.
- The Zhao source yielded 2,317 individually administered peptides from 352 patients (313 positives). Known exact training-overlap union exclusion removed two positive records; 2,315 records, 311 positives and 131 positive-bearing patients remained.
- The frozen 2,000-replicate primary comparison found BigMHC above PRIME by 0.057 patient-macro NDCG@5 (95% CI 0.008–0.106) and above DeepHLApan by 0.078 (0.022–0.133) on near-complete common support. DeepImmuno-CNN covered 43.8%; its common-support differences were unresolved.
- The BigMHC–PRIME direction reversed relative to IMPROVE. This is interpreted as model-by-domain dependence, not a universal-winner result. The vaccine-elicited post-vaccination ELISPOT endpoint remains distinct from natural tumor presentation and clinical benefit.

## 2026-08-20 — External-cohort funnel audit (third/fourth queue)

- Added `research/external_cohort_funnel.csv` and `research/external_cohort_failure_protocols.json` to preserve a source-by-source eligibility funnel rather than treating literature mentions as datasets.
- Screened ten candidates spanning IMPROVE, Zhao, NCI, RCC PCV, EVX-01, GBM NeoVax, melanoma personal vaccines, NEPdb, TESLA and ITSNdb. Zhao and IMPROVE remain the only currently verified eligible patient-grouped benchmark datasets in this repository; Zhao has already been frozen and run.
- NCI, GBM NeoVax, melanoma personal-vaccine data, NEPdb and ITSNdb received explicit failure reasons. NCI remains the decisive example of the mandatory rule: enumerated or untested short candidates are not experimental negatives.
- RCC PCV and EVX-01 remain `pending` rather than eligible because the public evidence establishes individual-peptide assay components but does not yet verify the complete patient–peptide–HLA row-level negative contract, exact HLA semantics and machine-readable redistribution path.
- No new predictions were launched from a pending source. The next safe action is a targeted supplement-member audit followed by a new frozen protocol only if every eligibility field passes.

## 2026-08-20 — RCC member audit and EVX-01 exclusion

- RCC Supplementary Table 2 was downloaded from the official Nature member URL and checksum-pinned (`c113c42b...5d0c1`). Worksheet 2 contains 130 rows from 9 patients; every row has a short epitope, predicted HLA field, three peptide-stimulation replicates and three no-stimulation replicates. RCC is therefore eligible as an endpoint-distinct vaccine cohort, and `research/extension_protocol_rcc_v1.json` was frozen before prediction.
- RCC is not untreated and its HLA values are predicted binding alleles; all downstream reporting must preserve those limitations. It cannot be merged with IMPROVE as natural presentation or with Zhao as an identical assay endpoint.
- EVX-01 was excluded after source-level audit. The paper reports 91 individually restimulated long vaccine peptides, but the public evidence does not provide a complete short-peptide-HLA row table with experimentally defined pMHC negatives; its background is an irrelevant peptide control. No prediction was run for EVX-01.

## 2026-08-20 — RCC extension prediction and evaluation completed

- Built `data/processed/rcc_vaccine_benchmark.csv` from 129 retained rows after excluding one N/A short-epitope/HLA source row; 9 patients, 75 positives and 54 negatives. Source checksum and row-level provenance are retained in `data/rcc_vaccine_summary.json` and the canonical rows.
- Training-overlap audit found zero exact PRIME2, published BigMHC construction, or DeepImmuno peptide-HLA overlaps; near-sequence results are retained, and DeepHLApan training identity remains unknown.
- Fixed predictors ran with coverage: BigMHC 128/129, PRIME 128/129, DeepHLApan 128/129, DeepImmuno-CNN 51/129. Missing outputs were not imputed or treated as negatives.
- Existing evaluation produced descriptive pooled AUROC / patient NDCG@5: BigMHC 0.476 / 0.533, PRIME 0.580 / 0.691, DeepHLApan 0.505 / 0.614, DeepImmuno-CNN 0.472 / 0.711. Unequal support, vaccine endpoint, predicted-HLA semantics and small patient count prohibit universal ranking claims.

## 2026-08-20 — Public predictor reproduction sweep

- Added `scripts/reproduce_public_predictors.py` to clone each queued public repository, capture the immutable HEAD revision and license-file paths, create a per-predictor Python 3.11 environment, run editable installation, and preserve install/smoke stdout, stderr, and JSON receipts.
- MHCnuggets, NeoFox, pVACtools, Vaxrank, and mhcmatch installed successfully. MHCnuggets and NeoFox passed import smoke tests; pVACtools and Vaxrank passed `--help`. mhcmatch has no documented smoke entry point in the checked revision.
- NeoGuider did not expose a Python package entry point (`pyproject.toml`/`setup.py` absent), and Seq2Neo requires TensorFlow 2.3.0, which has no Python 3.11 wheel. These are recorded as reproducibility failures, not silently repaired.
- pVACtools, NeoFox, Vaxrank, and Seq2Neo remain profile-only or non-comparable because their output contracts are end-to-end/annotation/ranking workflows rather than the canonical peptide–HLA score contract. No new candidate entered the benchmark.
- Follow-up MHCnuggets audit: production BA weights and curated training tables are present in the pinned repository. The official three-peptide example ran successfully under Python 3.11/TensorFlow and the strict adapter produced 3/3 binding scores with lower-IC50-is-better semantics. The repository's `saves/test/HLA-A01:01_test_model` is a separate test checkpoint whose expected values cannot validate the production checkpoint; this is recorded as a limitation rather than an exact-match claim. The predictor remains pending for binding-track inclusion until training-overlap and benchmark-task alignment are audited.
- Efficiency correction: mhcmatch's first binder invocation triggered its expensive calibration/reference bootstrap and timed out at 180 seconds. The cheap local CLI/API smoke path (`--help`, `decompose`) passed; the timeout is retained as evidence of an external/reference-data dependency, and no further large bootstrap was attempted for this profile-only candidate.
## 2026-08-20 — Cross-dataset stability and model-selection-risk analysis

Implemented `scripts/analyze_stability.py` and generated `results/analysis/stability/` from the frozen IMPROVE and Zhao benchmark/prediction artifacts. The analysis is explicitly exploratory/descriptive heterogeneity analysis: it produces a dataset × predictor × metric matrix, record-level Spearman ranking concordance, patient-bootstrap probability of being first at Recall@5, BigMHC–PRIME direction-reversal probability, and coverage-threshold common-support summaries. It uses analytic fixed-score rankings and a recorded seed; it does not perform post-hoc significance testing, causal inference, or clinical efficacy claims. The script preserves predictor status metadata and writes `analysis_metadata.json` with limitations and configuration.

Acceptance follow-up: added explicit `leave_one_domain_out.csv`, `endpoint_domain_metadata.csv`, a dependency-free endpoint/domain AUROC SVG, and `tests/test_stability_analysis.py`. First-place probabilities are task-stratified so presentation and immunogenicity predictors are not placed in one leaderboard. The expensive 2,000-bootstrap output remains the authoritative model-selection file; the leave-one-domain-out and visualization artifacts are deterministic post-processing of the frozen inputs.
