# NeoRepro agent instructions

## Authority

- Treat `PROJECT_PROMPT.md` as the user-authored project brief.
- Treat `RESEARCH_SPEC.md` as the current scientific contract. Update it only with a dated rationale in `research/research_log.md`.
- Never treat generated literature notes, model output, or search snippets as verified evidence.

## Reusable skills

Use the narrowest applicable skill:

- `$neorepro-literature-audit`: current literature, predictor landscape, novelty, scope.
- `$neorepro-data-audit`: benchmark ingestion, provenance, HLA/label normalization, leakage.
- `$neorepro-predictor-repro`: installation attempts, failure capture, adapters, registry.
- `$neorepro-benchmark`: pilot/full evaluation, patient metrics, statistics, figures.
- `$neorepro-paper-audit`: manuscript, citations, reviewer simulation, final reproduction audit.

Run bundled deterministic scripts before recreating equivalent one-off code.

## Scientific integrity

- Do not invent citations, data, results, software status, licenses, or biological conclusions.
- Open and verify the source supporting each factual claim. Store a stable identifier and access date.
- Use `unknown` when evidence is unavailable. Missing evidence is not negative evidence.
- Preserve failed and excluded predictors with explicit reasons.
- Distinguish computational performance from clinical efficacy.
- Do not treat untested candidates as experimental negatives.
- Do not call grouped descriptive evaluation patient-held-out or study-held-out validation.

## Engineering

- Keep predictor environments isolated and revisions pinned.
- Never print, log, store, or commit credentials. Read optional credentials only from environment variables.
- Store raw-source manifests and checksums; do not redistribute restricted data or weights.
- Generate manuscript tables and figures from versioned result files.
- Add tests for schemas, normalization, metrics, ranking, adapters, and provenance.
- Keep commands non-interactive and paths repository-relative.

## Gates

1. Do not scale beyond the cheap pilot until novelty, data eligibility, adapters, and metric fixtures pass.
2. Do not interpret full results until missing predictions, leakage, score direction, and grouping are audited.
3. Do not declare completion until a clean-checkout reproduction and manuscript audit pass.

