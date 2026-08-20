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
