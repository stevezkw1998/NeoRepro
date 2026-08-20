#!/usr/bin/env python3
"""Pinned, vectorized DeepImmuno-CNN adapter without fuzzy HLA rescue."""

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
from tensorflow import keras
from tensorflow.keras import layers

VERSION = "1.0@df42ac5b"
REVISION = "df42ac5b6bddfe531268335e2dcb496559cd488b"
FIELDS = ["record_id", "predictor", "predictor_version", "task", "score", "score_direction", "status"]
AMINO = "ARNDCQEGHILKMFPSTWYV-"


def canonical_hla(value: str) -> str:
    compact = re.sub(r"[^A-Z0-9]", "", value.upper().removeprefix("HLA"))
    match = re.fullmatch(r"([ABC])(\d{2})(\d{2})", compact)
    return f"HLA-{match.group(1)}*{match.group(2)}{match.group(3)}" if match else ""


def model() -> keras.Model:
    peptide = keras.Input(shape=(10, 12, 1))
    hla = keras.Input(shape=(46, 12, 1))
    x = layers.Conv2D(16, (2, 12))(peptide)
    x = layers.BatchNormalization()(x); x = layers.Activation("relu")(x)
    x = layers.Conv2D(32, (2, 1))(x)
    x = layers.BatchNormalization()(x); x = layers.Activation("relu")(x)
    x = layers.MaxPool2D((2, 1), strides=(2, 1))(x); x = layers.Flatten()(x)
    y = layers.Conv2D(16, (15, 12))(hla)
    y = layers.BatchNormalization()(y); y = layers.Activation("relu")(y)
    y = layers.MaxPool2D((2, 1), strides=(2, 1))(y)
    y = layers.Conv2D(32, (9, 1))(y)
    y = layers.BatchNormalization()(y); y = layers.Activation("relu")(y)
    y = layers.MaxPool2D((2, 1), strides=(2, 1))(y); y = layers.Flatten()(y)
    z = layers.Concatenate()([x, y]); z = layers.Dense(128, activation="relu")(z)
    z = layers.Dropout(0.2)(z); z = layers.Dense(1, activation="sigmoid")(z)
    return keras.Model([peptide, hla], z)


def encode(sequence: str, matrix: np.ndarray) -> np.ndarray:
    return np.stack([matrix[:, AMINO.index("-" if aa == "X" else aa)] for aa in sequence.upper()])


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = args.source_dir.resolve()
    observed = subprocess.run(["git", "rev-parse", "HEAD"], cwd=source, check=True, capture_output=True, text=True).stdout.strip()
    if observed != REVISION:
        raise RuntimeError(f"expected DeepImmuno {REVISION}, found {observed}")
    with args.input.open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    pca = np.loadtxt(source / "data/after_pca.txt").T
    table = pd.read_csv(source / "data/hla2paratopeTable_aligned.txt", sep="\t")
    hlas = {canonical_hla(str(row.HLA)): str(row.pseudo) for row in table.itertuples()}
    eligible = [(row, canonical_hla(row["hla"])) for row in rows if len(row["peptide"]) in {9, 10} and canonical_hla(row["hla"]) in hlas]
    scores: dict[str, float] = {}
    if eligible:
        peptides = np.stack([encode(row["peptide"] if len(row["peptide"]) == 10 else row["peptide"][:5] + "-" + row["peptide"][5:], pca) for row, _ in eligible])[..., None]
        hla_values = np.stack([encode(hlas[hla], pca) for _, hla in eligible])[..., None]
        network = model()
        # The upstream checkpoint prefix is the empty basename inside this
        # directory (`.index` / `.data-*`), so the trailing slash is material.
        network.load_weights(str(source / "models/cnn_model_331_3_7") + "/").expect_partial()
        values = network.predict([peptides, hla_values], batch_size=512, verbose=0).reshape(-1)
        scores = {row["record_id"]: float(value) for (row, _), value in zip(eligible, values, strict=True)}
    output = []
    for row in rows:
        hla = canonical_hla(row["hla"])
        value = scores.get(row["record_id"])
        status = "unsupported_length" if len(row["peptide"]) not in {9, 10} else "unsupported_hla" if hla not in hlas else "predicted" if value is not None and math.isfinite(value) else "invalid_output"
        output.append({"record_id": row["record_id"], "predictor": "DeepImmuno-CNN", "predictor_version": VERSION, "task": "immunogenicity", "score": f"{value:.12g}" if status == "predicted" else "", "score_direction": "higher", "status": status})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n"); writer.writeheader(); writer.writerows(output)
    print(f"DeepImmuno-CNN {VERSION}: {sum(r['status']=='predicted' for r in output)}/{len(output)} rows predicted -> {args.output}")
    return 0


if __name__ == "__main__":
    tf.get_logger().setLevel("ERROR")
    raise SystemExit(main())
