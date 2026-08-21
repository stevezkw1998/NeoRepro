# NeoRepro: a leakage-aware, patient-level, reproducible benchmark resource for public MHC-I peptide–HLA predictors

**Kewen Zhu** · Independent Researcher · [ORCID 0009-0001-9964-9090](https://orcid.org/0009-0001-9964-9090)

## Abstract

### Background

Public availability of a neoantigen predictor does not ensure that its software, weights, dependencies and inference contract remain reproducible, or that published tools can be compared without training overlap and support bias. We developed NeoRepro as a leakage-aware, patient-level benchmark resource for public MHC-I peptide–HLA predictors.

### Methods

We pinned five public predictors in isolated environments; harmonized a presentation-prefiltered patient-matched pMHC multimer screen and two endpoint-distinct personalized-vaccine ELISPOT cohorts; and versioned record provenance, known training-overlap classifications, standardized prediction adapters and failures. Comparisons used common prediction support, pooled discrimination, patient-level Top-K retrieval, patient bootstrap, support-matched random ranking and transparent held-out baselines.

### Results

All five pinned predictors produced outputs within their declared input support. The initial 520-row TESLA fixture was entirely training-overlapped and was retained only as a leakage-positive reproduction test. After excluding 45 exact PRIME2 overlaps from 17,520 IMPROVE records, 17,475 records from 70 patients remained. On common support, PRIME achieved AUROC 0.597 and mean pMHC-pair Recall@20 0.260 among 60 positive-bearing patients, versus 0.546 and 0.146 for BigMHC. Transparent peptide baselines outperformed HLA-only baselines under both patient- and study-held-out fitting, while adding HLA to peptide features did not consistently improve over peptide features alone. A frozen extension evaluated five models on 2,315 overlap-filtered vaccine peptides with a distinct post-vaccination ELISPOT endpoint. A second endpoint-distinct vaccine cohort contributed 129 individually assayed short peptides from 9 patients. Support-matched and cross-domain analyses showed that high marginal Top-K values did not necessarily imply stable or useful ranking signal.

### Conclusions

NeoRepro converts public predictor comparisons into an inspectable resource in which source records, versions, exclusions, missingness and result claims are machine-traceable. Leakage and support auditing materially changed interpretation, while fixed public scores showed only modest, context-dependent retrieval beyond appropriate references. The benchmark applies to already selected candidate sets and does not establish clinical utility.

## Introduction

Personalized neoantigen selection is a multi-stage problem: a mutated peptide must be generated, presented by a patient's HLA molecules and recognized by T cells. Predictors consequently target different estimands, including binding, presentation and T-cell recognition, and should not be collapsed into an undifferentiated leaderboard. MHCflurry 2.0 models class-I presentation [@odonnell2020mhcflurry], PRIME2 models T-cell recognition after presentation [@gfeller2023prime2], and BigMHC uses presentation pretraining followed by immunogenicity transfer learning [@albert2023bigmhc].

The TESLA consortium demonstrated prospective patient-specific testing and ranking of predicted candidates [@wells2020tesla]. Subsequent work harmonized patient datasets for model development and ranking [@muller2023harmonized], while IMPROVE released patient-matched T-cell recognition outcomes across 70 patients and three cohorts [@borch2024improve]. NeoGuider evaluated an end-to-end model across seven cohorts [@zhao2025neoguider], and T-SCAPE developed a cross-domain immunogenicity predictor [@kim2025tscape]. Zhao and colleagues released 2,317 individually administered short vaccine peptides from 352 patients and compared peptide features and presentation-related scores against post-vaccination ELISPOT measurements [@zhao2026vaccine]. Executable MHC-I benchmarking also predates this study in a comprehensively mapped model system [@paul2020benchmark]. Thus neither patient-level ranking nor multi-tool benchmarking is itself novel. These resources nevertheless create a risk that an apparently external benchmark has entered a predictor's training set, and they rarely make current artifact installability, record-level overlap, common support and patient-level uncertainty jointly auditable. A recent cross-task analysis further showed that HLA identity alone can exploit label imbalance in common immunogenicity benchmarks [@zhang2026shortcut].

NeoRepro asks a narrower question than developing a new predictor: what evidence remains usable when public artifacts are version-pinned, failures and workarounds are preserved, candidate records are evaluated on identical support, known training overlap is removed, and pooled performance is paired with patient-level retrieval? Its contribution is an executable measurement resource: canonical patient-linked records with source provenance; row-level overlap and missingness audits; standardized adapters with pinned revisions and isolated environments; and machine-generated metrics, figures and manifests that can be reproduced under documented upstream access and license conditions. We preserve the distinction between prediction tasks and reserve held-out terminology for models fitted within the declared split.

## Methods

### Study design and reproducibility contract

The core protocol was frozen in `RESEARCH_SPEC.md`; the Zhao extension and primary NDCG@5 endpoint were separately frozen in `research/extension_protocol.json`, and the RCC cohort in `research/extension_protocol_rcc_v1.json`, before their respective inference runs. Each predictor was assigned a pinned source revision, isolated environment, legal-access record, standardized adapter and evidence directory. Failed attempts were retained. MHCflurry 2.2.1 was run as a presentation predictor; BigMHC v1.0, PRIME 2.0, DeepImmuno-CNN and DeepHLApan were run as immunogenicity predictors. Scores were oriented so that larger values indicate stronger predicted evidence. No missing prediction was imputed.

### Dataset construction and provenance

We downloaded the data archive associated with IMPROVE from its pinned public repository revision and transformed `01_Validated_neoepitopes.txt` into a canonical record-level schema. Each row retains patient, study, peptide, HLA, experimental label, source revision, URL and source-row provenance. Candidates had already been filtered using MuPeXI, RNA-expression evidence and NetMHCpan 4.0 RankEL, with study-specific exceptions when candidate counts were limited [@borch2024improve]. The endpoint was DNA-barcoded pMHC multimer-detectable, patient-matched T-cell recognition; it does not demonstrate natural processing, tumor-surface presentation, effector function or killing. The schema's `immunogenicity` column is an operational field name for this endpoint, not intrinsic peptide immunogenicity. We normalized class-I HLA names and preserved patient-specific labels; conflicting outcomes for the same peptide–HLA in different patients were treated as context-dependent observations, not clerical duplicates.

For the independent extension, we extracted checksum-pinned `Table1.xlsx` from the Zhao 2026 Europe PMC supplement and retained 2,317 individually administered 8–11mer peptides from 352 patients [@zhao2026vaccine]. Source patient blocks were deterministically forward-filled; 55 reported ratios of “≥5.0” were preserved as right-censored lower bounds. Positivity followed the source threshold, post-vaccination/pre-vaccination IFN-γ ELISPOT ratio ≥2.0. This vaccine-elicited endpoint is distinct from the IMPROVE multimer screen and cannot establish natural tumor presentation or clinical efficacy.

The administered peptides had been selected by the source workflow using earlier NetMHC/NetMHCpan binding predictions and an IC50 threshold below 500 nM [@zhao2026vaccine]. Consequently, this cohort evaluates reranking within a predictor-enriched candidate set rather than unselected tumor mutations. Reported peptide–HLA restrictions were computational assignments used by the source analysis and were not individually established by HLA-blocking experiments.

For the endpoint-distinct RCC extension, we checksum-pinned Supplementary Table 2 from Braun and colleagues and retained 129 short-peptide rows from nine vaccinated patients after excluding one row without a usable short peptide/HLA assignment [@braun2025rcc]. Every retained row contained three peptide-stimulation and three matched no-stimulation replicates. Positivity followed the source individual-peptide p-value rule. The HLA field denotes the source-predicted best short-epitope allele; these rows therefore evaluate post-vaccination, in-vitro restimulation responses and cannot establish untreated intrinsic immunogenicity or natural tumour presentation.

### Training-overlap policy

The official PRIME2 supplementary archive and Table S4 workbook were downloaded by stable article identifier and checksum [@gfeller2023prime2]. We compared canonical peptides, peptide–HLA pairs and labels against every benchmark record and indexed same-HLA, same-length Hamming-distance-one training neighbors. Because the public BigMHC construction incorporates non-random PRIME1/2 peptide records of eligible length into immunogenicity training/validation, those exact matches were flagged separately [@albert2023bigmhc]. A single union exclusion of all exact PRIME2 peptide–HLA matches defined the common benchmark because peptide specificity is HLA-conditioned; peptides seen only with another HLA received a separate exclusion sensitivity, as did one-substitution neighbors. PRIME2 Table S4 lacks source mutation, patient and study identifiers, so those overlap dimensions are explicitly unavailable rather than assumed absent. The full benchmark and row-level audit remain versioned.

### Fixed-tool and transparent-baseline analyses

Every fixed tool scored all common benchmark records. MHCflurry was invoked with peptide and HLA only because source flanking sequences were unavailable; its output is therefore not a complete processing model and was not evaluated against presentation ground truth. Pooled metrics were AUROC and average precision; squared error was retained only as a descriptive machine-readable output, not a calibration comparison. The primary ranking unit was a tested patient–peptide–HLA (pMHC) record. For the 60 patients retaining at least one detected response, we calculated Recall@5/10/20, Precision@5/10/20, HitRate@5/10/20, mean reciprocal rank and NDCG@5/10/20. Metrics use expectation over ties at the Top-K boundary. The ten patients with no positive record were excluded from recall-based summaries by definition; no claim is made about their false-positive burden without a prospective decision threshold. Confidence intervals and paired differences used 2,000 patient bootstrap replicates with seed 20260820.

As a decision-unit sensitivity analysis, we collapsed records to unique patient–peptide candidates. A peptide was positive if any tested HLA pairing was positive, and its predictor score was the maximum oriented score across tested HLA pairings. We also restricted the fixed-tool analysis to 9–10mers, the public BigMHC immunogenicity training length domain. These deterministic sensitivity analyses do not identify which HLA would mediate a response.

To distinguish fixed pretrained tools from models with known splitting, we fitted transparent class-weighted logistic-regression baselines using one-hot HLA identity, peptide length and amino-acid composition, or both. All preprocessing and fitting occurred within leave-one-patient-out (LOPO) or leave-one-study-out (LOSO) folds. These baselines are diagnostic controls, not proposed predictors. Their patient-bootstrap intervals are conditional on the frozen out-of-fold predictions and do not include refitting variation. With only three studies, LOSO results are reported as three observed held-out domains rather than inference to a population of studies.

### Resource packaging, sensitivity and quality control

The resource stores canonical schemas, source-row provenance, predictor and dataset registries, standardized prediction files, overlap classifications, model-support tables, paired comparisons, figures and a SHA-256 result manifest. A machine-validated extension contract defines Dataset Cards, Predictor Cards and prediction artifacts, while the expanded artifact census preserves successful, non-comparable and failed public-tool attempts. Third-party artifacts that cannot be redistributed are obtained from their official locations under their original terms. We reported per-study and per-HLA metrics, performance after replacing scores by within-HLA ranks, performance of HLA mean scores alone, and the score-scale-specific, unadjusted fraction of observed score variance lying between HLA groups. Cross-dataset stability and first-place probabilities are explicitly exploratory and task-stratified. Per-HLA tables include record, positive, patient and study support, and mark rows with fewer than three positives or three patients as unsupported for interpretation. HLA analyses are exploratory; no permutation p-values are used for biological inference. Deterministic unit tests cover schema counts, hashes, score direction, missingness, tie handling and metric fixtures. Pooled AUROC and average precision were cross-checked against scikit-learn, and the documented workflow was rerun from a clean checkout.

## Results

### Public-artifact reproduction

The version-pinned CPU workflows for MHCflurry 2.2.1, BigMHC v1.0 and PRIME 2.0 all produced complete outputs for the common benchmark. Reproduction nevertheless required tool-specific workarounds: MHCflurry model-path correction, a 4.6-GB BigMHC repository checkout and native rebuilding of PRIME and MixMHCpred binaries on Apple Silicon. These observations are recorded in `data/predictor_registry.csv`; they describe this platform and these pinned revisions rather than a universal installation-success rate.

### Leakage audit changed the benchmark

All 520 records in the TESLA pilot exactly matched a peptide–HLA pair in the official PRIME2 training table with concordant labels; all also satisfied the public BigMHC immunogenicity training-set construction. We therefore retained TESLA only as a leakage-positive reproduction fixture. The public IMPROVE source contained 17,520 rows, 467 T-cell-recognized records, 70 patients and 3 cohorts. Its audit identified 45 exact PRIME2 peptide–HLA overlaps, including 7 label conflicts; 43 met the BigMHC immunogenicity training construction. Union exclusion removed all 45 exact PRIME2 overlaps and retained 17,475 records, 465 positives and 70 patients. Mutation, patient and study overlap were unavailable in the PRIME2 training table and are explicitly marked unknown. Among retained records, 35 had a peptide seen in PRIME2 training only with another HLA; excluding them yielded AUROC 0.545 for BigMHC and 0.596 for PRIME. A further 18 records had a same-HLA, same-length PRIME2 training peptide one substitution away. Removing them yielded nearly unchanged AUROC for BigMHC (0.546) and PRIME (0.596). Exact and one-substitution non-overlap still cannot rule out undocumented or representation-level training influence.

### Fixed public predictors

Table 1 reports the two fixed scores in the same broad immunogenicity category on identical records. The primary comparison was pooled AUROC. The analytic random-ranking reference for mean pMHC-pair Recall@20 was 0.103. PRIME exceeded BigMHC by 0.051 AUROC (patient-bootstrap 95% CI 0.008–0.092 for PRIME minus BigMHC). PRIME also had higher mean pMHC-pair Recall@20 among 60 positive-bearing patients (0.260, conditional 95% CI 0.187–0.342) than BigMHC (0.146, 0.098–0.204). MHCflurry is a peptide/HLA-only presentation invocation without presentation ground truth; its descriptive association with T-cell detection was AUROC 0.537, AP 0.032 and pMHC-pair Recall@20 0.202. It is not ranked as an immunogenicity competitor. Patient retrieval varied substantially (Figure 2).

**Table 1. Fixed public immunogenicity scores on the common overlap-filtered benchmark.** AP is average precision. Patient confidence intervals use 2,000 resamples of patients and are conditional on the fixed predictions.

| Predictor | Task | AUROC | AP | Mean Recall@20 (95% patient-bootstrap CI) |
|---|---|---:|---:|---:|
| BigMHC | immunogenicity | 0.546 | 0.032 | 0.146 (0.098–0.204) |
| PRIME | immunogenicity | 0.597 | 0.040 | 0.260 (0.187–0.342) |

### Decision-unit and length-domain sensitivity

The 17,475 pMHC records represented 15,508 unique patient–peptide candidates; 1,601 candidates had multiple tested HLA pairings and 101 had discordant labels across HLA. After any-HLA-positive label aggregation and maximum raw-score aggregation, Recall@20 was 0.166 for BigMHC, 0.220 for MHCflurry and 0.304 for PRIME. Because raw score scales depend on HLA, this aggregation is exploratory. Normalizing scores to empirical within-HLA mid-percentiles before taking the maximum gave Recall@20 of 0.202, 0.215 and 0.240, respectively. Thus the decision unit and cross-HLA score rule changed absolute retrieval but not the qualitative ordering. Restriction to 9–10mers retained 15,234 records and yielded AUROC 0.547 for BigMHC and 0.605 for PRIME, preserving the primary direction.

Expanding the same 9–10mer IMPROVE subset to the two newly reproduced models gave AUROC 0.527 on 11,036 supported records for DeepImmuno-CNN and 0.508 on all 15,234 records for DeepHLApan, versus 0.605 for PRIME. Their patient NDCG@5 values were 0.021, 0.023 and 0.102, respectively. This secondary expanded-model analysis used 500 patient bootstrap replicates and does not alter the frozen 2,000-replicate external primary analysis.

### Patient- and study-held-out transparent baselines

Under leave-one-patient-out (LOPO) fitting, peptide logistic regression achieved AUROC 0.628 and mean Recall@20 0.212, compared with 0.562 and 0.121 for HLA-only logistic regression. The HLA-plus-peptide model reached AUROC 0.634, but its paired AUROC difference from peptide only was not resolved by the conditional 95% interval. Under leave-one-study-out (LOSO) fitting, peptide only again exceeded HLA only (AUROC 0.619 versus 0.546); adding HLA yielded 0.595. These comparisons use the same estimator and differ only in feature set. The three study-specific LOSO results are descriptive, not a population-of-studies inference (Figure 3 and `results/analysis/improve/baselines/`).

**Table 2. Transparent baselines fitted with the declared held-out unit.** Patient-bootstrap intervals are conditional on the frozen out-of-fold predictions and omit fitting variation.

| Predictor | Task | AUROC | AP | Mean Recall@20 (95% patient-bootstrap CI) |
|---|---|---:|---:|---:|
| HLA+peptide LR LOPO | immunogenicity_lopo | 0.634 | 0.049 | 0.206 (0.147–0.273) |
| HLA-only LR LOPO | immunogenicity_lopo | 0.562 | 0.038 | 0.121 (0.088–0.157) |
| Peptide LR LOPO | immunogenicity_lopo | 0.628 | 0.047 | 0.212 (0.150–0.279) |
| HLA+peptide LR LOSO | immunogenicity_loso | 0.595 | 0.043 | 0.172 (0.123–0.228) |
| HLA-only LR LOSO | immunogenicity_loso | 0.546 | 0.033 | 0.119 (0.084–0.158) |
| Peptide LR LOSO | immunogenicity_loso | 0.619 | 0.045 | 0.191 (0.137–0.251) |

### HLA and cohort sensitivity

Within-HLA rank AUROC was 0.546, 0.575 and 0.603 for MHCflurry, BigMHC and PRIME, respectively. HLA mean scores alone were near or below chance (0.466, 0.480 and 0.505). The score-scale-specific fraction of observed variance lying between HLA groups was 0.112, 0.325 and 0.060; it is not interpreted as an isolated allele effect or compared across arbitrary score transformations. BigMHC cohort AUROC ranged from 0.511 to 0.644. With only three compound domains, cohort results cannot separate cancer, treatment, assay and HLA composition.

### Independent vaccine-cohort extension

The frozen extension contained 2,317 individually administered 8–11mer peptides from 352 patients. Known exact-overlap union exclusion removed 2 records (2 positives), retaining 2,315 records, 311 positives and 131 positive-bearing patients. The audit found 2 exact PRIME2 matches and 0 exact DeepImmuno matches; DeepHLApan row-level training identity remains unknown.

The prospectively frozen primary metric was patient-macro NDCG@5 because the median patient had six candidates and Recall@20 would saturate. Table 3 reports each immunogenicity model together with the exact expectation for a tied random score on that model's support. On full support, random NDCG@5 was 0.578; BigMHC exceeded that reference by 0.081, whereas DeepHLApan's gain was 0.002. DeepImmuno-CNN's apparently high marginal NDCG@5 was 0.755 on 43.8% coverage, compared with a support-matched random expectation of 0.759. Pairwise comparisons used model-specific common support and 2,000 patient bootstrap replicates. The BigMHC-minus-PRIME NDCG@5 difference on common support was 0.057 (unadjusted 95% CI 0.008–0.106); this within-cohort contrast is not a formal cross-dataset interaction test. MHCflurry remains a task-distinct presentation association control.

**Table 3. Independent Zhao 2026 vaccine-cohort extension.** The endpoint is post-vaccination IFN-γ ELISPOT after peptide-pulsed dendritic-cell administration, not natural tumor presentation or clinical efficacy.

| Predictor | Predicted records | AUROC | AP | Patient NDCG@5 (95% CI) | Random NDCG@5 | Gain over random |
|---|---:|---:|---:|---:|---:|---:|
| BigMHC | 2,315 | 0.550 | 0.148 | 0.658 (0.606–0.707) | 0.578 | 0.081 |
| DeepHLApan | 2,315 | 0.488 | 0.131 | 0.580 (0.524–0.635) | 0.578 | 0.002 |
| DeepImmuno-CNN | 1,015 | 0.526 | 0.158 | 0.755 (0.691–0.816) | 0.759 | -0.004 |
| PRIME | 2,310 | 0.531 | 0.148 | 0.604 (0.546–0.660) | 0.581 | 0.023 |

### Endpoint-distinct RCC vaccine cohort

The separately frozen RCC protocol retained 129 individually assayed short peptides from 9 vaccinated patients after excluding one source row with no usable short peptide/HLA assignment [@braun2025rcc]. The assay compared three peptide-stimulation replicates with three matched no-stimulation replicates; labels follow the source p-value threshold and therefore are assay-context outcomes rather than untreated biological negatives. No exact PRIME2, BigMHC-construction or DeepImmuno training overlap was identified among the 129 records, while DeepHLApan row-level training identity remains unknown.

On near-complete support, PRIME had AUROC 0.580 and patient NDCG@5 0.691; BigMHC had 0.476 and 0.533, respectively. DeepImmuno-CNN supported only 51 records. With nine patients, all estimates are descriptive and do not establish a cross-domain interaction, universal ordering, natural tumour presentation or clinical efficacy.

**Table 4. RCC personalized-vaccine cohort.** The endpoint is post-vaccination, individual-peptide IFN-γ ELISpot after in-vitro stimulation. Random NDCG@5 is calculated on each model's exact support.

| Predictor | Predicted records | AUROC | AP | Patient NDCG@5 (95% CI) | Random NDCG@5 | Gain over random |
|---|---:|---:|---:|---:|---:|---:|
| BigMHC | 128 | 0.476 | 0.586 | 0.533 (0.418–0.640) | 0.587 | -0.054 |
| DeepHLApan | 128 | 0.505 | 0.653 | 0.614 (0.407–0.765) | 0.587 | 0.027 |
| DeepImmuno-CNN | 51 | 0.472 | 0.583 | 0.711 (0.591–0.839) | 0.695 | 0.016 |
| PRIME | 128 | 0.580 | 0.639 | 0.691 (0.611–0.789) | 0.587 | 0.104 |

### Expanded reproducibility profile and extension contract

The artifact census now records 12 pinned predictor entries. Beyond the five benchmarked tools, 7 entries are retained as profile-only, non-comparable, pending or unreproducible outcomes rather than being silently omitted. The public extension contract supplies machine-validated Dataset Cards, Predictor Cards and prediction-artifact schemas together with a common-support evaluator; these additions improve reuse but do not make heterogeneous prediction tasks scientifically interchangeable.


### Reusable benchmark outputs

NeoRepro's primary output is the versioned evidence chain rather than a winner label. Each benchmark record can be traced to a source row and overlap classification; each score records predictor version, task, direction and status; model comparisons use explicit common support; and all reported numerical outputs are generated from frozen result files. The resource also preserves the fully overlapped TESLA fixture and failed NCI eligibility gate as negative controls, so future evaluations can test whether leakage and invalid-label safeguards behave as intended. Metric validation agreed with an independent implementation to floating-point precision, and clean-checkout reproduction regenerated the frozen outputs.

Figures 1–6 are generated from frozen result files: fixed predictor performance, patient Recall@20, held-out baselines, HLA sensitivity, the Zhao vaccine-cohort extension and exploratory endpoint/domain stability, respectively (`results/figures/` and `results/analysis/stability/`).

## Discussion

NeoRepro's central contribution is a reusable measurement contract. The first seemingly convenient benchmark, TESLA, reproduced the initial tools but was completely overlapped with the official PRIME2 training table and the published BigMHC immunogenicity data construction. Without an explicit overlap audit, those results would have looked like external validation. Retaining it as a leakage-positive fixture makes that failure detectable. Moving to IMPROVE and applying one common exclusion retained most records while preventing predictor-specific support from determining the comparison.

The benchmark's biological results are deliberately secondary to that contract. On the filtered IMPROVE common set, PRIME showed better pooled and patient-level point estimates than BigMHC within the same broad peptide–HLA immunogenicity-score category. Their training labels and score contracts differ, so this is an observation about the pinned implementations and evaluation contract, not evidence of universal superiority. MHCflurry addresses presentation rather than T-cell recognition, was invoked without flanking context, and was tested only for association with the recognition endpoint; its results cannot validate presentation performance. All absolute average-precision values were low in a highly imbalanced screen, and patient-level pMHC retrieval varied widely.

The vaccine cohorts illustrate why support and task context belong in the resource. In Zhao, BigMHC had the largest positive NDCG@5 gain over random ranking among the near-complete-support immunogenicity models, while DeepHLApan was approximately at its random reference. DeepImmuno-CNN covered less than half of Zhao and RCC, and high marginal NDCG@5 on restricted support cannot be read as a general advantage. RCC was smaller still, with only nine patients. A paired BigMHC–PRIME contrast favored BigMHC for Zhao NDCG@5, whereas RCC and IMPROVE produced different point-estimate patterns. No formal dataset-by-model interaction was tested, and the reported pairwise intervals were not adjusted for multiple comparisons. We therefore do not claim a statistically established cross-domain ranking reversal. The defensible observation is narrower: model conclusions depend on endpoint, metric and supported candidate set, and no evaluated score was a stable universal winner.

The transparent baselines refine interpretation of HLA effects. HLA-only models exceeded chance modestly under LOPO but weakened under LOSO, consistent with cohort- and allele-associated label structure. Peptide features supplied more stable signal; adding HLA did not consistently improve beyond them. For BigMHC, 32.5% of observed score variance lay between HLA groups, but this unadjusted quantity also mixes peptide composition, patient, cohort and preselection; it is not an isolated allele effect. HLA sensitivity therefore requires more than one shortcut diagnostic.

This study has important limitations. IMPROVE candidates were preselected through a presentation-oriented pipeline and are not a random sample of tumor mutations; the Zhao and RCC peptides were likewise selected within vaccine-design workflows. Our analysis therefore tests reranking after candidate-selection gates, not end-to-end discovery from all tumor variants. Experimental nonresponse is assay-, sample- and context-dependent, not proof that a peptide can never be immunogenic. PBMC, TIL and, in one cohort, TIL-ACT infusion-product sampling are not separated in the released canonical inputs used here. Identical peptide–HLA pairs had conflicting outcomes across patients, directly showing that recognition is not a deterministic function of the model inputs; treatment, tumor microenvironment and TCR repertoire were not modeled. Only three cohorts support the original IMPROVE LOSO analysis, and cohort simultaneously changes cancer, treatment, sample source and candidate-generation context. RCC adds only nine vaccinated patients and uses predicted HLA assignments. One positive-bearing patient in the IMPROVE source data lost all positives after common overlap exclusion, leaving 60 patients for ranking. Exact matching cannot detect undocumented training data or representation overlap. The five benchmarked tools are a judicious executable subset; the broader census includes heterogeneous tools that cannot be placed into the same comparison. All cover only MHC-I here and require different inputs and licenses. BigMHC and PRIME use only mutant peptide and HLA here, without wild-type counterpart, expression, clonality or direct presentation evidence, so they do not measure complete neoantigen quality. The vaccine extensions are biologically complementary rather than pure replications: vaccination and ex-vivo or in-vitro stimulation can induce or amplify responses absent in untreated disease, reported HLA restrictions were not individually proven experimentally, and DeepHLApan's public repository lacks a row-level training manifest. The clean reproduction is demonstrated on the documented platform, while upstream availability and platform compatibility can change. Finally, no computational benchmark here establishes vaccine efficacy, treatment response or clinical benefit.

The practical implication is that neoantigen benchmarking should release source-grounded record identifiers, predictor versions, complete missingness, training-overlap audits, support-matched references and patient-level retrieval alongside pooled metrics. NeoRepro provides these components as an executable resource that can be extended with new datasets or predictors without erasing negative results. Its value is not a new ranking algorithm or a universal leaderboard; it is a reproducible way to determine which comparison claims survive provenance, leakage, support and patient-level checks.

## Data and code availability

NeoRepro code, canonical schemas, audit outputs, complete redistributable prediction files, metrics, tables, figures and a SHA-256 result manifest are available in the [public GitHub repository](https://github.com/stevezkw1998/NeoRepro). Release v0.1.1 is permanently archived at [Zenodo DOI 10.5281/zenodo.22037064](https://doi.org/10.5281/zenodo.22037064). The source download workflow retrieves third-party data and predictors from pinned public locations, verifies checksums where stable, and requires users to accept applicable upstream terms. Third-party predictors and data retain their original licenses; the repository does not redistribute or relicense PRIME or other restricted upstream artifacts.

## Ethics statement

This secondary computational analysis used publicly released pseudonymized study records and performed no new human-subject intervention. Ethical approvals and consent for the original samples are described in the source studies.

## Competing interests

To be completed by the submitting authors.

## Funding

To be completed by the submitting authors.

## References

Bibliographic records are stored in `paper/references.bib`.
