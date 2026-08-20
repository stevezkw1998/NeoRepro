# MHCflurry 2.2.1 reproduction

- Source revision: `6afbf04312b247d4c1e46dc14902d20faa92e893`
- Package: `mhcflurry==2.2.1`
- Download release: `2.2.0`, `models_class1_presentation`
- License: Apache-2.0
- Primary output: presentation score (higher is prioritized)

The adapter supplies exactly one HLA allele per benchmark record and explicitly passes the downloaded model directory. It does not treat all alleles observed for a patient as a genotype because the source table labels each peptide-HLA observation separately.

The first two custom-download attempts are intentionally retained in `attempts/`: setting `MHCFLURRY_DOWNLOADS_DIR` causes release resolution to become `None` in 2.2.1. The working command instead sets `MHCFLURRY_DATA_DIR` and `MHCFLURRY_DOWNLOADS_CURRENT_RELEASE`.

Downloaded models and the isolated environment are excluded from Git. Run the documented setup target before invoking the adapter on a clean checkout.
