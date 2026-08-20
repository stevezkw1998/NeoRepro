# NeoRepro novelty and scope decision

Date: 2026-08-20

Decision: **RESCOPE, then GO to a cheap pilot**

## Already addressed

Patient-level neoantigen ranking is not new by itself. TESLA compared 25 team pipelines across six subjects using AUPRC, fraction-ranked and Top-20 immunogenic fraction. Later studies reused TESLA for patient-wise comparisons, and ITSNdb compared seven software families with Top-10/Top-20 analyses in a simulated prioritization scenario.

HLA shortcut bias is also no longer an open discovery claim. A 2026 Cell Genomics study showed that HLA-only models can exploit allele-specific label imbalance in current immunogenicity benchmarks.

Recent work further narrows the performance gap: NeoGuider reports multi-cohort patient evaluation; TransNRank reports improved Top-20 recall; NEAT learns real expert vaccine-selection decisions and is integrated into pVACtools v7.

## Unresolved gap

No verified study in the audited set combines all of the following as primary outputs:

1. a contemporaneous, version-pinned attempt to install and run multiple public neoantigen scoring tools from their public artifacts;
2. a preserved failure taxonomy covering dependency rot, missing weights/data, unclear licenses, invalid links and platform constraints;
3. standardized reruns on identical peptide–HLA records with explicit missing-output and common-support accounting;
4. comparison of pooled discrimination with patient-level ranking under patient bootstrap;
5. study-, HLA- and known-training-overlap sensitivity analyses;
6. a clean, open reproduction harness that generates the tables and manuscript from raw predictions.

This is a resource and measurement contribution, not a claim to invent patient-level metrics or a new biological predictor.

## Final scope

NeoRepro will use two linked tracks:

### Track A — public-artifact reproducibility profile

Maintain a broad landscape of citable public tools and record legal access, installability, runtime success, dependency age, documentation quality and failure evidence. End-to-end pipelines remain in this track even when they cannot enter a peptide-only score comparison.

### Track B — comparable MHC-I peptide–HLA score benchmark

Run a smaller set of locally executable, public scoring methods on the same experimentally tested candidate records. The initial TESLA pilot preserves six subject groupings, but the official PRIME2 training table revealed that all 520 pilot rows were exact training records for PRIME2 and met BigMHC's immunogenicity-training construction. TESLA is therefore a leakage-positive reproduction fixture, not the primary performance benchmark.

The primary patient-level dataset is now the public IMPROVE screen: 17,520 experimentally screened records from 70 source-grounded patients and three cohorts. A common leakage filter removes 45 exact PRIME2 peptide–HLA overlaps, leaving 17,475 rows for fixed-tool comparison. The full and filtered manifests remain versioned.

Pretrained predictors cannot honestly receive a new “study-held-out” label unless their training data and model fitting support that claim. For fixed pretrained tools, NeoRepro will report cross-study external performance and known/unknown training overlap. True patient-held-out or study-held-out training will be reserved for transparent baselines fitted within NeoRepro.

## Cheap pilot

Attempt these scientifically distinct public tools first:

1. MHCflurry 2.0 presentation score — maintained open baseline;
2. BigMHC-IM — open immunogenicity model with CPU inference and public weights;
3. PRIME 2.0 — compact immunogenicity model, contingent on license and platform compatibility.

Use a small TESLA subset to verify schema conversion, score direction, allele handling, missingness and patient-level metrics. DeepImmuno and DeepHLApan are high-value dependency-rot follow-ups if the pilot pipeline works.

## Novel contribution claimed

The defensible contribution is a reproducibility dataset plus a fair rerun: which public tools still run, what fails and why, whether conclusions depend on shared evaluable rows, and whether pooled metric rankings agree with patient-level prioritization. Any bias or performance result will be reported as an observed replication, extension or null result—not as a predetermined discovery.

## Threats to novelty

- A fast-moving 2026 literature landscape may produce another reproducibility benchmark before submission.
- IMPROVE candidate screening was conditioned on predicted presentation, so the benchmark does not represent all tumor mutations.
- Exact overlap removal cannot establish absence of near-sequence, feature-level, or undocumented training influence.
- Only three source cohorts are available for study-level sensitivity analysis.
- Tool tasks differ; binding, presentation, immunogenicity and end-to-end ranking must not be collapsed into one leaderboard.

Re-run the novelty audit before full-scale experiments and before venue selection.
