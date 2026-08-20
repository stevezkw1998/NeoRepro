# NeoRepro: leakage-aware reproduction of public MHC-I predictors on a presentation-prefiltered T-cell recognition screen

**Author line:** to be completed before submission

## Abstract

### Background

Public availability of a neoantigen predictor at publication does not ensure that its software, weights, dependencies and inference contract remain reproducible or that published tools can be compared without training overlap. We developed NeoRepro as an auditable reproduction and evaluation harness for public MHC-I peptide–HLA predictors.

### Methods

We pinned and reproduced three distinct public predictors, harmonized a presentation-prefiltered patient-matched pMHC multimer screen, audited training overlap, and evaluated complete common-support predictions. We report association with multimer-detectable T-cell recognition, patient-level pMHC-pair Top-K retrieval with patient bootstrap, unique-peptide and length-domain sensitivity analyses, cohort and HLA sensitivity, plus transparent baselines fitted by leave-one-patient-out and leave-one-study-out splits.

### Results

{{AUTO_ABSTRACT_RESULTS}}

### Conclusions

Reproduction evidence and leakage auditing materially changed the interpretation of this benchmark. Fixed public scores retained modest association with observed T-cell recognition after exact-overlap exclusion, but retrieval was heterogeneous across patients and cohorts. Results apply only to candidates already selected by a presentation-oriented pipeline. The study supports auditable, task-aware evaluation; it does not establish clinical utility.

## Introduction

Personalized neoantigen selection is a multi-stage problem: a mutated peptide must be generated, presented by a patient's HLA molecules and recognized by T cells. Predictors consequently target different estimands, including binding, presentation and T-cell recognition, and should not be collapsed into an undifferentiated leaderboard. MHCflurry 2.0 models class-I presentation [@odonnell2020mhcflurry], PRIME2 models T-cell recognition after presentation [@gfeller2023prime2], and BigMHC uses presentation pretraining followed by immunogenicity transfer learning [@albert2023bigmhc].

The TESLA consortium demonstrated prospective patient-specific testing and ranking of predicted candidates [@wells2020tesla]. The later IMPROVE study released patient-matched T-cell recognition outcomes across 70 patients and three cohorts [@borch2024improve]. These resources make patient-level evaluation possible, but they also create a risk that an apparently external benchmark has entered a predictor's training set. A recent cross-task analysis further showed that HLA identity alone can exploit label imbalance in common immunogenicity benchmarks [@zhang2026shortcut].

NeoRepro asks a narrower question than developing a new predictor: what conclusions remain when public artifacts are version-pinned, failures and workarounds are preserved, candidate records are evaluated on identical support, known training overlap is removed, and pooled performance is compared with patient-level retrieval? We treat reproducibility and negative evidence as study outcomes, preserve the distinction between prediction tasks, and reserve held-out terminology for models fitted within the declared split.

## Methods

### Study design and reproducibility contract

The protocol was frozen in `RESEARCH_SPEC.md` before full inference. Each predictor was assigned a pinned source revision, isolated environment, legal-access record, standardized adapter and evidence directory. Failed attempts were retained. MHCflurry 2.2.1 was run as a presentation predictor; BigMHC v1.0 and PRIME 2.0 were run as immunogenicity predictors. Scores were oriented so that larger values indicate stronger predicted evidence. No missing prediction was imputed as a favorable or unfavorable score.

### Dataset construction and provenance

We downloaded the data archive associated with IMPROVE from its pinned public repository revision and transformed `01_Validated_neoepitopes.txt` into a canonical record-level schema. Each row retains patient, study, peptide, HLA, experimental label, source revision, URL and source-row provenance. Candidates had already been filtered using MuPeXI, RNA-expression evidence and NetMHCpan 4.0 RankEL, with study-specific exceptions when candidate counts were limited [@borch2024improve]. The endpoint was DNA-barcoded pMHC multimer-detectable, patient-matched T-cell recognition; it does not demonstrate natural processing, tumor-surface presentation, effector function or killing. The schema's `immunogenicity` column is an operational field name for this endpoint, not intrinsic peptide immunogenicity. We normalized class-I HLA names and preserved patient-specific labels; conflicting outcomes for the same peptide–HLA in different patients were treated as context-dependent observations, not clerical duplicates.

### Training-overlap policy

The official PRIME2 supplementary archive and Table S4 workbook were downloaded by stable article identifier and checksum [@gfeller2023prime2]. We compared canonical peptides, peptide–HLA pairs and labels against every benchmark record and indexed same-HLA, same-length Hamming-distance-one training neighbors. Because the public BigMHC construction incorporates non-random PRIME1/2 peptide records of eligible length into immunogenicity training/validation, those exact matches were flagged separately [@albert2023bigmhc]. A single union exclusion of all exact PRIME2 peptide–HLA matches defined the common benchmark because peptide specificity is HLA-conditioned; peptides seen only with another HLA received a separate exclusion sensitivity, as did one-substitution neighbors. PRIME2 Table S4 lacks source mutation, patient and study identifiers, so those overlap dimensions are explicitly unavailable rather than assumed absent. The full benchmark and row-level audit remain versioned.

### Fixed-tool and transparent-baseline analyses

Every fixed tool scored all common benchmark records. MHCflurry was invoked with peptide and HLA only because source flanking sequences were unavailable; its output is therefore not a complete processing model and was not evaluated against presentation ground truth. Pooled metrics were AUROC and average precision; squared error was retained only as a descriptive machine-readable output, not a calibration comparison. The primary ranking unit was a tested patient–peptide–HLA (pMHC) record. For the 60 patients retaining at least one detected response, we calculated Recall@5/10/20, Precision@5/10/20, HitRate@5/10/20, mean reciprocal rank and NDCG@5/10/20. Metrics use expectation over ties at the Top-K boundary. The ten patients with no positive record were excluded from recall-based summaries by definition; no claim is made about their false-positive burden without a prospective decision threshold. Confidence intervals and paired differences used 2,000 patient bootstrap replicates with seed 20260820.

As a decision-unit sensitivity analysis, we collapsed records to unique patient–peptide candidates. A peptide was positive if any tested HLA pairing was positive, and its predictor score was the maximum oriented score across tested HLA pairings. We also restricted the fixed-tool analysis to 9–10mers, the public BigMHC immunogenicity training length domain. These deterministic sensitivity analyses do not identify which HLA would mediate a response.

To distinguish fixed pretrained tools from models with known splitting, we fitted transparent class-weighted logistic-regression baselines using one-hot HLA identity, peptide length and amino-acid composition, or both. All preprocessing and fitting occurred within leave-one-patient-out (LOPO) or leave-one-study-out (LOSO) folds. These baselines are diagnostic controls, not proposed predictors. Their patient-bootstrap intervals are conditional on the frozen out-of-fold predictions and do not include refitting variation. With only three studies, LOSO results are reported as three observed held-out domains rather than inference to a population of studies.

### Sensitivity and quality control

We reported per-study and per-HLA metrics, performance after replacing scores by within-HLA ranks, performance of HLA mean scores alone, and the score-scale-specific, unadjusted fraction of observed score variance lying between HLA groups. Per-HLA tables include record, positive, patient and study support, and mark rows with fewer than three positives or three patients as unsupported for interpretation. HLA analyses are exploratory; no permutation p-values are used for biological inference. Deterministic unit tests cover schema counts, hashes, score direction, missingness, tie handling and metric fixtures. Pooled AUROC and average precision were cross-checked against scikit-learn.

## Results

{{AUTO_RESULTS}}

Figures 1–4 are generated from frozen result files: fixed predictor performance, patient Recall@20, held-out baselines and HLA sensitivity, respectively (`results/figures/`).

## Discussion

NeoRepro's central result is procedural as much as predictive. The first seemingly convenient benchmark, TESLA, reproduced all three tools but was completely overlapped with the official PRIME2 training table and the published BigMHC immunogenicity data construction. Without an explicit overlap audit, those results would have looked like external validation. Moving to IMPROVE and applying one common exclusion retained most records while preventing predictor-specific support from determining the comparison.

On the filtered common set, PRIME showed better pooled and patient-level point estimates than BigMHC within the same broad peptide–HLA immunogenicity-score category. Their training labels and score contracts differ, so this is an observation about the pinned implementations, dataset and evaluation contract, not evidence of universal superiority. MHCflurry addresses presentation rather than T-cell recognition, was invoked without flanking context, and was tested only for association with the recognition endpoint; its results cannot validate presentation performance. All absolute average-precision values were low in a highly imbalanced screen, and patient-level pMHC retrieval varied widely.

The transparent baselines refine interpretation of HLA effects. HLA-only models exceeded chance modestly under LOPO but weakened under LOSO, consistent with cohort- and allele-associated label structure. Peptide features supplied more stable signal; adding HLA did not consistently improve beyond them. For BigMHC, 32.5% of observed score variance lay between HLA groups, but this unadjusted quantity also mixes peptide composition, patient, cohort and preselection; it is not an isolated allele effect. HLA sensitivity therefore requires more than one shortcut diagnostic.

This study has important limitations. IMPROVE candidates were preselected through a presentation-oriented pipeline and are not a random sample of tumor mutations; our analysis tests reranking after this gate, not end-to-end discovery from all tumor variants. Experimental nonresponse is assay-, sample- and context-dependent, not proof that a peptide can never be immunogenic. PBMC, TIL and, in one cohort, TIL-ACT infusion-product sampling are not separated in the released canonical inputs used here. Identical peptide–HLA pairs had conflicting outcomes across patients, directly showing that recognition is not a deterministic function of the model inputs; treatment, tumor microenvironment and TCR repertoire were not modeled. Only three cohorts support LOSO analysis, and cohort simultaneously changes cancer, treatment, sample source and candidate-generation context. One positive-bearing patient in the source data lost all positives after common overlap exclusion, leaving 60 patients for ranking. Exact matching cannot detect undocumented training data or representation overlap. The three tools cover only MHC-I and require different inputs and licenses. BigMHC and PRIME use only mutant peptide and HLA here, without wild-type counterpart, expression, clonality or direct presentation evidence, so they do not measure complete neoantigen quality. Finally, no computational benchmark establishes vaccine efficacy, treatment response or clinical benefit.

The practical implication is that neoantigen benchmarking should release source-grounded record identifiers, predictor versions, complete missingness, training-overlap audits and patient-level retrieval alongside pooled metrics. NeoRepro provides a compact harness for that purpose and exposes where the evidence remains uncertain.

## Data and code availability

NeoRepro code, canonical schemas, audit outputs, complete prediction files, metrics, tables, figures and a SHA-256 result manifest are included in the repository. The source download script retrieves third-party data from pinned public locations and verifies checksums. Third-party predictors and data retain their original licenses; the repository does not relicense PRIME or other upstream artifacts.

## Ethics statement

This secondary computational analysis used publicly released pseudonymized study records and performed no new human-subject intervention. Ethical approvals and consent for the original samples are described in the source studies.

## Competing interests

To be completed by the submitting authors.

## Funding

To be completed by the submitting authors.

## References

Bibliographic records are stored in `paper/references.bib`.
