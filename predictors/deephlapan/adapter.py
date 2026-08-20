#!/usr/bin/env python3
"""Pinned DeepHLApan adapter with a documented TensorFlow-2 compatibility shim."""

from __future__ import annotations

import argparse
import csv
import math
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import tensorflow as tf

VERSION = "1.1.1@ac1f4beb"
REVISION = "ac1f4bebc095271504dfc2d2a93888df3be94e83"
FIELDS = ["record_id", "predictor", "predictor_version", "task", "score", "score_direction", "status", "binding_score"]
AA = {aa: index + 1 for index, aa in enumerate("ACDEFGHIKLMNPQRSTVWY")}; AA["X"] = 21


def canonical_hla(value: str) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", value.upper().removeprefix("HLA"))
    match = re.fullmatch(r"([ABC])(\d{2})(\d{2})", compact)
    return f"HLA-{match.group(1)}{match.group(2)}:{match.group(3)}" if match else ""


class LegacyGRU(tf.keras.layers.GRU):
    def __init__(self, *args, reset_after=False, **kwargs):
        super().__init__(*args, reset_after=False, **kwargs)


class Attention(tf.keras.layers.Layer):
    def __init__(self, W_regularizer=None, b_regularizer=None, W_constraint=None, b_constraint=None, bias=True, return_attention=False, **kwargs):
        super().__init__(**kwargs); self.supports_masking = True; self.return_attention = return_attention; self.bias = bias
        self.init = tf.keras.initializers.get("glorot_uniform"); self.W_regularizer = tf.keras.regularizers.get(W_regularizer); self.b_regularizer = tf.keras.regularizers.get(b_regularizer); self.W_constraint = tf.keras.constraints.get(W_constraint); self.b_constraint = tf.keras.constraints.get(b_constraint)
    def build(self, shape):
        self.W = self.add_weight(shape=(shape[-1],), initializer=self.init, name=f"{self.name}_W", regularizer=self.W_regularizer, constraint=self.W_constraint)
        self.b = self.add_weight(shape=(shape[1],), initializer="zeros", name=f"{self.name}_b", regularizer=self.b_regularizer, constraint=self.b_constraint) if self.bias else None
        super().build(shape)
    def call(self, x, mask=None):
        e = tf.squeeze(tf.matmul(x, tf.expand_dims(self.W, -1)), -1)
        if self.b is not None: e += self.b
        a = tf.exp(tf.tanh(e))
        if mask is not None: a *= tf.cast(mask, a.dtype)
        a /= tf.reduce_sum(a, axis=1, keepdims=True) + tf.keras.backend.epsilon()
        result = tf.reduce_sum(x * tf.expand_dims(a, -1), axis=1)
        return [result, a] if self.return_attention else result
    def compute_output_shape(self, shape):
        return [(shape[0], shape[-1]), (shape[0], shape[1])] if self.return_attention else (shape[0], shape[-1])


def ensemble(model_dir: Path, prefix: str, values: np.ndarray) -> np.ndarray:
    predictions = []
    for index in range(1, 6):
        network = tf.keras.models.load_model(model_dir / f"{prefix}_model{index}.hdf5", custom_objects={"Attention": Attention, "GRU": LegacyGRU}, compile=False)
        predictions.append(network.predict(values, batch_size=512, verbose=0).reshape(-1))
        tf.keras.backend.clear_session()
    return np.mean(predictions, axis=0)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    observed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, check=True, capture_output=True, text=True).stdout.strip()
    if observed != REVISION: raise RuntimeError(f"expected DeepHLApan {REVISION}, found {observed}")
    with args.input.open(newline="", encoding="utf-8-sig") as handle: rows = list(csv.DictReader(handle))
    table = pd.read_csv(source / "deephlapan/model/MHC_pseudo.dat", sep="\t")
    hlas = {str(row.HLA): str(row.sequence) for row in table.itertuples()}
    eligible = [(row, canonical_hla(row["hla"])) for row in rows if 8 <= len(row["peptide"]) <= 14 and canonical_hla(row["hla"]) in hlas]
    immuno: dict[str, float] = {}; binding: dict[str, float] = {}
    if eligible:
        values = np.full((len(eligible), 49), 21, dtype=np.int32)
        for index, (row, hla) in enumerate(eligible):
            sequence = hlas[hla] + row["peptide"].upper()
            values[index, :len(sequence)] = [AA[aa] for aa in sequence]
        model_dir = source / "deephlapan/model"
        i_values = ensemble(model_dir, "immunogenicity", values); b_values = ensemble(model_dir, "binding", values)
        immuno = {row["record_id"]: float(value) for (row, _), value in zip(eligible, i_values, strict=True)}
        binding = {row["record_id"]: float(value) for (row, _), value in zip(eligible, b_values, strict=True)}
    output = []
    for row in rows:
        hla = canonical_hla(row["hla"]); value = immuno.get(row["record_id"]); bvalue = binding.get(row["record_id"])
        status = "unsupported_length" if not 8 <= len(row["peptide"]) <= 14 else "unsupported_hla" if hla not in hlas else "predicted" if value is not None and math.isfinite(value) else "invalid_output"
        output.append({"record_id": row["record_id"], "predictor": "DeepHLApan", "predictor_version": VERSION, "task": "immunogenicity", "score": f"{value:.12g}" if status == "predicted" else "", "score_direction": "higher", "status": status, "binding_score": f"{bvalue:.12g}" if status == "predicted" else ""})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(output)
    print(f"DeepHLApan {VERSION}: {sum(r['status']=='predicted' for r in output)}/{len(output)} rows predicted -> {args.output}")
    return 0


if __name__ == "__main__":
    tf.get_logger().setLevel("ERROR")
    raise SystemExit(main())
