# BigMHC v1.0 reproduction

- Source revision: `9d84a3b4da77c9253ac90ff8cb629274003b90fd`
- License: BigMHC Academic License (noncommercial use)
- Primary output: BigMHC-IM immunogenicity score (higher is prioritized)
- Secondary output: BigMHC-EL presentation score

The paper environment is reproduced with Python 3.9, PyTorch 1.13.0, Pandas 1.4.4, NumPy 1.21.5, SciPy 1.7.3, and scikit-learn 1.0.2. `psutil` is an undeclared runtime dependency imported by the CLI and is pinned here at 5.9.8.

The upstream v1.0 repository is approximately 4.6 GB because it includes model parameters. It is downloaded into an ignored directory and is not relicensed by NeoRepro. The official EL fixture reproduced within a maximum absolute score difference of `2.6e-7` on macOS ARM64 CPU.

BigMHC's `MHCEncoder` silently substitutes an unsupported HLA using prefix or Levenshtein matching. The NeoRepro adapter prevents that behavior by accepting only alleles found exactly in the pinned pseudosequence table after punctuation normalization; unsupported alleles receive an explicit missing status.
