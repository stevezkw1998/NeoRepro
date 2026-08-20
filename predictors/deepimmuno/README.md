# DeepImmuno-CNN adapter

The adapter pins upstream revision `df42ac5b6bddfe531268335e2dcb496559cd488b` and its published checkpoint. It supports only exact upstream HLA pseudosequences and 9–10mer peptides. Unlike upstream interactive code, it never substitutes an unrecognised allele with a nearby allele.

Run through `scripts/run_fixed_predictors.py`; install reproducibly through `scripts/setup_predictors.py --predictors deepimmuno`.
