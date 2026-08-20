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
