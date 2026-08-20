# DeepHLApan adapter

The adapter pins upstream revision `ac1f4bebc095271504dfc2d2a93888df3be94e83` and averages the five published immunogenicity and binding models. The original Keras-2 files encode legacy `GRU(reset_after=False)` layers; the compatibility shim preserves that setting while loading under TensorFlow 2.15. It never substitutes unsupported HLA alleles.

The public repository does not expose a row-level training manifest, so training overlap remains `unknown`, not zero.
