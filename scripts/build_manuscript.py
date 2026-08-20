#!/usr/bin/env python3
"""Build the NeoRepro manuscript from a template and frozen machine-readable results."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def f(value: float | str) -> str:
    return f"{float(value):.3f}"


def metric_table(rows: list[dict[str, str]]) -> str:
    lines = [
        "| Predictor | Task | AUROC | AP | Mean Recall@20 (95% patient-bootstrap CI) |",
        "|---|---|---:|---:|---:|",
    ]
    for row in rows:
        recall = f(row["recall@20"])
        low = f(row["recall@20_ci_low"])
        high = f(row["recall@20_ci_high"])
        lines.append(
            f"| {row['predictor']} | {row['task']} | {f(row['auroc'])} | "
            f"{f(row['average_precision'])} | {recall} ({low}–{high}) |"
        )
    return "\n".join(lines)


def build_results(root: Path) -> tuple[str, str]:
    full = load_json(root / "data/improve_summary.json")
    filtered = load_json(root / "data/improve_leakage_filter_summary.json")
    tesla = load_json(root / "research/training_overlap_summary.json")
    improve = load_json(root / "research/training_overlap_summary_improve.json")
    fixed_sensitivity = load_json(root / "data/improve_fixed_sensitivity_summary.json")
    fixed_result = load_json(root / "results/analysis/improve/fixed/metrics.json")
    peptide_result = load_json(root / "results/analysis/improve/peptide_sensitivity/metrics.json")
    peptide_hla_rank_result = load_json(
        root / "results/analysis/improve/peptide_sensitivity_hla_rank/metrics.json"
    )
    exact_peptide_result = load_json(
        root / "results/analysis/improve/exact_peptide_free/metrics.json"
    )
    near_result = load_json(root / "results/analysis/improve/near_overlap_free/metrics.json")
    length_result = load_json(root / "results/analysis/improve/length_9_10/metrics.json")
    fixed = load_csv(root / "results/tables/fixed_predictor_summary.csv")
    baselines = load_csv(root / "results/tables/heldout_baseline_summary.csv")
    hla = {row["predictor"]: row for row in load_csv(root / "results/analysis/improve/hla_sensitivity.csv")}
    benchmark_groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in load_csv(root / "data/processed/improve_benchmark.csv"):
        benchmark_groups[row["patient_id"]].append(row)
    positive_groups = [
        rows for rows in benchmark_groups.values() if any(int(row["immunogenicity"]) for row in rows)
    ]
    random_recall20 = mean(min(20, len(rows)) / len(rows) for rows in positive_groups)

    by_name = {row["predictor"]: row for row in fixed}
    prime = by_name["PRIME"]
    bigmhc = by_name["BigMHC"]
    paired = next(
        row
        for row in fixed_result["paired_same_task"]
        if row["left"] == "BigMHC" and row["right"] == "PRIME" and row["metric"] == "auroc"
    )
    abstract = (
        f"All three pinned predictors ran to completion. The initial {tesla['benchmark_rows']}-row "
        "TESLA fixture was entirely training-overlapped and was not used for performance claims. "
        f"After excluding {filtered['excluded_exact_prime2_peptide_hla_rows']} exact PRIME2 overlaps "
        f"from {full['rows']:,} IMPROVE records, {filtered['retained_rows']:,} records from "
        f"{filtered['retained_patients']} patients remained. On the common set, PRIME achieved AUROC "
        f"{f(prime['auroc'])} and mean pMHC-pair Recall@20 {f(prime['recall@20'])} among 60 "
        "positive-bearing patients, versus "
        f"{f(bigmhc['auroc'])} and {f(bigmhc['recall@20'])} for BigMHC. Transparent peptide "
        "baselines outperformed HLA-only baselines under both patient- and study-held-out fitting, "
        "while adding HLA to peptide features did not consistently improve over peptide features alone."
    )

    lopo = {row["predictor"]: row for row in baselines if row["analysis"] == "lopo"}
    loso = {row["predictor"]: row for row in baselines if row["analysis"] == "loso"}
    peptide_metrics = peptide_result["metrics"]
    peptide_hla_rank_metrics = peptide_hla_rank_result["metrics"]
    exact_peptide_metrics = exact_peptide_result["metrics"]
    near_metrics = near_result["metrics"]
    length_metrics = length_result["metrics"]
    results = f"""### Public-artifact reproduction

The version-pinned CPU workflows for MHCflurry 2.2.1, BigMHC v1.0 and PRIME 2.0 all produced complete outputs for the common benchmark. Reproduction nevertheless required tool-specific workarounds: MHCflurry model-path correction, a 4.6-GB BigMHC repository checkout and native rebuilding of PRIME and MixMHCpred binaries on Apple Silicon. These observations are recorded in `data/predictor_registry.csv`; they describe this platform and these pinned revisions rather than a universal installation-success rate.

### Leakage audit changed the benchmark

All {tesla['benchmark_rows']} records in the TESLA pilot exactly matched a peptide–HLA pair in the official PRIME2 training table with concordant labels; all also satisfied the public BigMHC immunogenicity training-set construction. We therefore retained TESLA only as a leakage-positive reproduction fixture. The public IMPROVE source contained {full['rows']:,} rows, {full['positives']} T-cell-recognized records, {full['patients']} patients and {full['cohorts']} cohorts. Its audit identified {improve['benchmark_record_classifications']['exact_label_concordant'] + improve['benchmark_record_classifications']['exact_label_conflict']} exact PRIME2 peptide–HLA overlaps, including {improve['benchmark_record_classifications']['exact_label_conflict']} label conflicts; {improve['benchmark_records_exact_bigmhc_im_trainval_overlap']} met the BigMHC immunogenicity training construction. Union exclusion removed all {filtered['excluded_exact_prime2_peptide_hla_rows']} exact PRIME2 overlaps and retained {filtered['retained_rows']:,} records, {filtered['retained_positives']} positives and {filtered['retained_patients']} patients. Mutation, patient and study overlap were unavailable in the PRIME2 training table and are explicitly marked unknown. Among retained records, {fixed_sensitivity['exact_peptide_free']['excluded_from_common_benchmark']} had a peptide seen in PRIME2 training only with another HLA; excluding them yielded AUROC {f(exact_peptide_metrics['BigMHC']['pooled']['auroc'])} for BigMHC and {f(exact_peptide_metrics['PRIME']['pooled']['auroc'])} for PRIME. A further {fixed_sensitivity['near_overlap_free']['excluded_from_common_benchmark']} records had a same-HLA, same-length PRIME2 training peptide one substitution away. Removing them yielded nearly unchanged AUROC for BigMHC ({f(near_metrics['BigMHC']['pooled']['auroc'])}) and PRIME ({f(near_metrics['PRIME']['pooled']['auroc'])}). Exact and one-substitution non-overlap still cannot rule out undocumented or representation-level training influence.

### Fixed public predictors

Table 1 reports the two fixed scores in the same broad immunogenicity category on identical records. The primary comparison was pooled AUROC. The analytic random-ranking reference for mean pMHC-pair Recall@20 was {f(random_recall20)}. PRIME exceeded BigMHC by {f(abs(paired['difference_left_minus_right']))} AUROC (patient-bootstrap 95% CI {f(abs(paired['ci_high']))}–{f(abs(paired['ci_low']))} for PRIME minus BigMHC). PRIME also had higher mean pMHC-pair Recall@20 among 60 positive-bearing patients ({f(prime['recall@20'])}, conditional 95% CI {f(prime['recall@20_ci_low'])}–{f(prime['recall@20_ci_high'])}) than BigMHC ({f(bigmhc['recall@20'])}, {f(bigmhc['recall@20_ci_low'])}–{f(bigmhc['recall@20_ci_high'])}). MHCflurry is a peptide/HLA-only presentation invocation without presentation ground truth; its descriptive association with T-cell detection was AUROC {f(by_name['MHCflurry']['auroc'])}, AP {f(by_name['MHCflurry']['average_precision'])} and pMHC-pair Recall@20 {f(by_name['MHCflurry']['recall@20'])}. It is not ranked as an immunogenicity competitor. Patient retrieval varied substantially (Figure 2).

**Table 1. Fixed public immunogenicity scores on the common overlap-filtered benchmark.** AP is average precision. Patient confidence intervals use 2,000 resamples of patients and are conditional on the fixed predictions.

{metric_table([bigmhc, prime])}

### Decision-unit and length-domain sensitivity

The {filtered['retained_rows']:,} pMHC records represented 15,508 unique patient–peptide candidates; 1,601 candidates had multiple tested HLA pairings and 101 had discordant labels across HLA. After any-HLA-positive label aggregation and maximum raw-score aggregation, Recall@20 was {f(peptide_metrics['BigMHC']['patient']['recall@20'])} for BigMHC, {f(peptide_metrics['MHCflurry']['patient']['recall@20'])} for MHCflurry and {f(peptide_metrics['PRIME']['patient']['recall@20'])} for PRIME. Because raw score scales depend on HLA, this aggregation is exploratory. Normalizing scores to empirical within-HLA mid-percentiles before taking the maximum gave Recall@20 of {f(peptide_hla_rank_metrics['BigMHC']['patient']['recall@20'])}, {f(peptide_hla_rank_metrics['MHCflurry']['patient']['recall@20'])} and {f(peptide_hla_rank_metrics['PRIME']['patient']['recall@20'])}, respectively. Thus the decision unit and cross-HLA score rule changed absolute retrieval but not the qualitative ordering. Restriction to 9–10mers retained {length_metrics['BigMHC']['pooled']['n']:,} records and yielded AUROC {f(length_metrics['BigMHC']['pooled']['auroc'])} for BigMHC and {f(length_metrics['PRIME']['pooled']['auroc'])} for PRIME, preserving the primary direction.

### Patient- and study-held-out transparent baselines

Under leave-one-patient-out (LOPO) fitting, peptide logistic regression achieved AUROC {f(lopo['Peptide LR LOPO']['auroc'])} and mean Recall@20 {f(lopo['Peptide LR LOPO']['recall@20'])}, compared with {f(lopo['HLA-only LR LOPO']['auroc'])} and {f(lopo['HLA-only LR LOPO']['recall@20'])} for HLA-only logistic regression. The HLA-plus-peptide model reached AUROC {f(lopo['HLA+peptide LR LOPO']['auroc'])}, but its paired AUROC difference from peptide only was not resolved by the conditional 95% interval. Under leave-one-study-out (LOSO) fitting, peptide only again exceeded HLA only (AUROC {f(loso['Peptide LR LOSO']['auroc'])} versus {f(loso['HLA-only LR LOSO']['auroc'])}); adding HLA yielded {f(loso['HLA+peptide LR LOSO']['auroc'])}. These comparisons use the same estimator and differ only in feature set. The three study-specific LOSO results are descriptive, not a population-of-studies inference (Figure 3 and `results/analysis/improve/baselines/`).

**Table 2. Transparent baselines fitted with the declared held-out unit.** Patient-bootstrap intervals are conditional on the frozen out-of-fold predictions and omit fitting variation.

{metric_table(baselines)}

### HLA and cohort sensitivity

Within-HLA rank AUROC was {f(hla['MHCflurry']['within_hla_rank_auroc'])}, {f(hla['BigMHC']['within_hla_rank_auroc'])} and {f(hla['PRIME']['within_hla_rank_auroc'])} for MHCflurry, BigMHC and PRIME, respectively. HLA mean scores alone were near or below chance ({f(hla['MHCflurry']['between_hla_mean_auroc'])}, {f(hla['BigMHC']['between_hla_mean_auroc'])} and {f(hla['PRIME']['between_hla_mean_auroc'])}). The score-scale-specific fraction of observed variance lying between HLA groups was {f(hla['MHCflurry']['score_variance_explained_by_hla'])}, {f(hla['BigMHC']['score_variance_explained_by_hla'])} and {f(hla['PRIME']['score_variance_explained_by_hla'])}; it is not interpreted as an isolated allele effect or compared across arbitrary score transformations. BigMHC cohort AUROC ranged from {f(min(value['auroc'] for value in fixed_result['metrics']['BigMHC']['study'].values()))} to {f(max(value['auroc'] for value in fixed_result['metrics']['BigMHC']['study'].values()))}. With only three compound domains, cohort results cannot separate cancer, treatment, assay and HLA composition.
"""
    return abstract, results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--template", type=Path, default=Path("paper/manuscript_template.md"))
    parser.add_argument("--output", type=Path, default=Path("paper/manuscript.md"))
    args = parser.parse_args()
    root = args.root.resolve()
    template = (root / args.template).read_text(encoding="utf-8")
    abstract, results = build_results(root)
    manuscript = template.replace("{{AUTO_ABSTRACT_RESULTS}}", abstract).replace(
        "{{AUTO_RESULTS}}", results
    )
    if "{{AUTO_" in manuscript:
        raise SystemExit("unresolved manuscript placeholder")
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(manuscript, encoding="utf-8")
    print(json.dumps({"output": str(args.output), "characters": len(manuscript)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
