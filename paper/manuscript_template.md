# NeoRepro: a leakage-aware, patient-level, reproducible benchmark resource for public MHC-I peptide–HLA predictors

**Kewen Zhu** · Independent Researcher · [ORCID 0009-0001-9964-9090](https://orcid.org/0009-0001-9964-9090)

## Abstract

### Background

Public availability of a neoantigen predictor does not ensure that its software, weights, dependencies and inference contract remain reproducible, or that published tools can be compared without training overlap and support bias. We developed NeoRepro as a leakage-aware, patient-level benchmark resource for public MHC-I peptide–HLA predictors.

### Methods

We pinned five public predictors in isolated environments; harmonized a presentation-prefiltered patient-matched pMHC multimer screen and two endpoint-distinct personalized-vaccine ELISPOT cohorts; and versioned record provenance, known training-overlap classifications, standardized prediction adapters and failures. Comparisons used common prediction support, pooled discrimination, patient-level Top-K retrieval, patient bootstrap, support-matched random ranking and transparent held-out baselines.

### Results

{{AUTO_ABSTRACT_RESULTS}}

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

{{AUTO_RESULTS}}

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
