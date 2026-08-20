# PRIME 2.0 reproduction

- PRIME revision: `ec1aa020089d62e9193ad377ddda9c93eed7f5b1`
- MixMHCpred revision: v2.2, `f64bb4548082768c70a1cfb5a4442d5e6ea04591`
- License: both are LICR academic non-commercial, non-transferable programs
- Primary output: allele-specific PRIME score (higher is prioritized)

The distributed macOS executables are x86-64 and cannot run natively on the tested ARM64 machine. NeoRepro locally recompiles both provided C++ sources with Apple Clang; those derived binaries and all upstream files stay in ignored directories and are never redistributed.

Both upstream Bash/Perl pipelines interpolate paths without robust quoting, and PRIME explicitly rejects input and output paths containing spaces. The repository root intentionally contains spaces and an em dash, so the adapter stages the licensed local copies in a temporary ASCII path, patches only the temporary wrapper paths, and deletes the staging copy after inference.

PRIME can score many alleles in one invocation. NeoRepro runs every eligible peptide against the union of observed alleles and extracts the score for that record's declared peptide-HLA pair, rather than the cross-allele `best` score.
