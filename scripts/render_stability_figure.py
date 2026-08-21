#!/usr/bin/env python3
"""Render a dependency-free SVG from the stability matrix."""
import csv
import html
from pathlib import Path

root=Path(__file__).resolve().parents[1]; out=root/"results/analysis/stability"; rows=list(csv.DictReader((out/"dataset_predictor_metric_matrix.csv").open()))
ds=sorted({r["dataset"] for r in rows}); names=sorted({r["predictor"] for r in rows}); W,H=900,100+len(names)*34; left,top,cell=220,55,110
def value(d,n):
    for r in rows:
        if r["dataset"]==d and r["predictor"]==n and r["metric"]=="AUROC": return float(r["value"])
    return None
def color(v):
    if v is None:return "#d9d9d9"
    q=max(0,min(1,v)); return f"rgb({int(245-180*q)},{int(245-120*q)},{int(245-20*q)})"
s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">', '<rect width="100%" height="100%" fill="white"/>', '<text x="20" y="25" font-family="Arial" font-size="18">Exploratory AUROC by endpoint/domain and predictor</text>']
for j,d in enumerate(ds): s += [f'<text x="{left+j*cell+8}" y="45" font-family="Arial" font-size="11">{html.escape(d)}</text>']
for i,n in enumerate(names):
    y=top+i*34; s.append(f'<text x="10" y="{y+22}" font-family="Arial" font-size="12">{html.escape(n)}</text>')
    for j,d in enumerate(ds):
        v=value(d,n); x=left+j*cell; s.append(f'<rect x="{x}" y="{y}" width="95" height="28" fill="{color(v)}" stroke="white"/>'); s.append(f'<text x="{x+47}" y="{y+19}" text-anchor="middle" font-family="Arial" font-size="11">{"NA" if v is None else f"{v:.3f}"}</text>')
s += [f'<text x="20" y="{H-12}" font-family="Arial" font-size="10">Fixed pretrained scores; descriptive heterogeneity only; endpoint/domain differences are not causal estimates.</text>','</svg>']
(out/"endpoint_domain_auroc.svg").write_text("\n".join(s)+"\n")
