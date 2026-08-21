import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/analysis/stability"


class StabilityAnalysisTest(unittest.TestCase):
    def test_stability_outputs_have_required_artifacts(self):
        required = [
            "dataset_predictor_metric_matrix.csv",
            "rank_stability.csv",
            "model_selection_first_probability.csv",
            "sensitivity_summary.csv",
            "leave_one_domain_out.csv",
            "endpoint_domain_metadata.csv",
            "analysis_metadata.json",
        ]
        self.assertTrue(all((OUT / name).exists() for name in required))
        meta = json.loads((OUT / "analysis_metadata.json").read_text())
        self.assertEqual(meta["analysis_type"], "exploratory_descriptive_heterogeneity")
        self.assertEqual(meta["bootstrap"], 2000)
        self.assertEqual(
            set(meta["datasets"]),
            {
                "improve_benchmark",
                "zhao_vaccine_benchmark",
                "rcc_vaccine_benchmark",
            },
        )

    def test_task_specific_first_probabilities_sum_to_one(self):
        rows = list(csv.DictReader((OUT / "model_selection_first_probability.csv").open()))
        for key in {(r["dataset"], r["task"], r["metric"]) for r in rows}:
            group = [
                float(r["probability_first"])
                for r in rows
                if (r["dataset"], r["task"], r["metric"]) == key
            ]
            self.assertAlmostEqual(sum(group), 1.0)

    def test_lodo_is_explicitly_descriptive(self):
        rows = list(csv.DictReader((OUT / "leave_one_domain_out.csv").open()))
        self.assertTrue(
            rows and {r["analysis_type"] for r in rows} == {"descriptive_leave_one_domain_out"}
        )
