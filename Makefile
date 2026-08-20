SHELL := /bin/zsh
export LC_ALL := en_US.UTF-8
export LANG := en_US.UTF-8
PY := uv run python

.PHONY: install setup-predictors download-improve build-improve audit-improve extension download-zhao build-zhao audit-zhao predict-zhao evaluate-zhao predict-expanded-improve evaluate-expanded-improve \
	predict-improve baselines-improve evaluate-improve hla-improve figures manuscript \
	sensitivity-improve build-peptide-sensitivity evaluate-peptide-sensitivity \
	evaluate-peptide-hla-rank-sensitivity build-fixed-sensitivities \
	evaluate-exact-peptide-sensitivity evaluate-near-sensitivity \
	evaluate-length-sensitivity manifest validate-metrics reproduce-results full-reproduce test \
	verify-reproduction validate-literature status readme-i18n-status check-readme-i18n

install:
	uv sync --extra dev --extra analysis

setup-predictors:
	$(PY) scripts/setup_predictors.py --accept-academic-licenses

download-improve:
	$(PY) scripts/download_public_data.py --source-id improve_patient_screen
	$(PY) scripts/download_archive_member.py \
		--url https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9811684/supplementaryFiles \
		--member mmc6.xlsx --sha256 641a104764167f9f04bafb6606e519e5625740ed1720af7d15ac9026636bc23a \
		--output data/raw/prime2_table_s4.xlsx

build-improve:
	$(PY) scripts/build_improve_benchmark.py \
		--archive data/raw/improve_patient_screen.zip \
		--output data/processed/improve_benchmark_full.csv \
		--summary data/improve_summary.json
	$(MAKE) audit-improve

audit-improve:
	$(PY) scripts/audit_prime2_overlap.py \
		--benchmark data/processed/improve_benchmark_full.csv \
		--supplement-zip data/raw/prime2_table_s4.xlsx \
		--output research/training_overlap_audit_improve.csv \
		--summary research/training_overlap_summary_improve.json \
		--source-url https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9811684/supplementaryFiles
	$(PY) scripts/filter_training_overlap.py \
		--benchmark data/processed/improve_benchmark_full.csv \
		--audit research/training_overlap_audit_improve.csv \
		--output data/processed/improve_benchmark.csv \
		--summary data/improve_leakage_filter_summary.json

predict-improve:
	$(PY) scripts/run_fixed_predictors.py \
		--input data/processed/improve_benchmark.csv \
		--output-dir results/raw_predictions/improve --parallel \
		--receipt reports/full_predictor_run.json --reuse-existing

download-zhao:
	$(PY) scripts/download_archive_member.py \
		--url https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13286890/supplementaryFiles \
		--member Table1.xlsx --sha256 1fa76cf45435c39dc28e9d52e584d56938cee531dda953ad11cfbcc9c2617aea \
		--output data/raw/zhao2026_table1.xlsx
	$(PY) scripts/download_archive_member.py \
		--url https://www.ebi.ac.uk/europepmc/webservices/rest/PMC9811684/supplementaryFiles \
		--member mmc6.xlsx --sha256 641a104764167f9f04bafb6606e519e5625740ed1720af7d15ac9026636bc23a \
		--output data/raw/prime2_table_s4.xlsx

build-zhao: download-zhao
	$(PY) scripts/build_vaccine_benchmark.py --input data/raw/zhao2026_table1.xlsx \
		--output data/processed/zhao_vaccine_benchmark_full.csv --summary data/zhao_vaccine_summary.json

audit-zhao: build-zhao
	$(PY) scripts/audit_external_training_overlap.py \
		--benchmark data/processed/zhao_vaccine_benchmark_full.csv \
		--prime2-archive data/raw/prime2_table_s4.xlsx \
		--deepimmuno-training predictors/deepimmuno/source/data/remove_low_negative/remove0123.csv \
		--output research/training_overlap_audit_zhao.csv \
		--summary research/training_overlap_summary_zhao.json
	$(PY) scripts/filter_known_training_overlap.py \
		--benchmark data/processed/zhao_vaccine_benchmark_full.csv \
		--audit research/training_overlap_audit_zhao.csv \
		--output data/processed/zhao_vaccine_benchmark.csv \
		--summary data/zhao_vaccine_leakage_filter_summary.json

predict-zhao: audit-zhao
	$(PY) scripts/run_fixed_predictors.py --input data/processed/zhao_vaccine_benchmark.csv \
		--output-dir results/raw_predictions/zhao \
		--predictors mhcflurry bigmhc prime deepimmuno deephlapan \
		--parallel --reuse-existing --receipt reports/zhao_predictor_run.json

evaluate-zhao: predict-zhao
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/zhao_vaccine_benchmark.csv \
		--predictions results/raw_predictions/zhao/*.csv \
		--output-dir results/analysis/zhao/fixed --bootstrap 2000 --seed 20260820
	$(PY) scripts/summarize_extension.py

predict-expanded-improve:
	$(PY) scripts/run_fixed_predictors.py --input data/sensitivity/length_9_10/benchmark.csv \
		--output-dir results/raw_predictions/improve/expanded_9_10 \
		--predictors deepimmuno deephlapan --parallel --reuse-existing \
		--receipt reports/improve_expanded_predictor_run.json

evaluate-expanded-improve: predict-expanded-improve
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/sensitivity/length_9_10/benchmark.csv \
		--predictions data/sensitivity/length_9_10/predictions/*.csv \
			results/raw_predictions/improve/expanded_9_10/*.csv \
		--output-dir results/analysis/improve/expanded_9_10 --bootstrap 500 --seed 20260820

extension: setup-predictors evaluate-zhao evaluate-expanded-improve
	$(MAKE) test

baselines-improve:
	$(PY) scripts/run_lopo_baselines.py \
		--input data/processed/improve_benchmark.csv \
		--output-dir results/raw_predictions/improve/baselines/lopo \
		--fold-manifest results/analysis/improve/lopo_folds.csv \
		--group-column patient_id
	$(PY) scripts/run_lopo_baselines.py \
		--input data/processed/improve_benchmark.csv \
		--output-dir results/raw_predictions/improve/baselines/loso \
		--fold-manifest results/analysis/improve/loso_folds.csv \
		--group-column study_id
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/baselines/lopo/*.csv \
		--output-dir results/analysis/improve/baselines/lopo --bootstrap 2000 --seed 20260820
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/baselines/loso/*.csv \
		--output-dir results/analysis/improve/baselines/loso --bootstrap 2000 --seed 20260820

evaluate-improve:
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/mhcflurry-2.2.1.csv \
			results/raw_predictions/improve/bigmhc-v1.0.csv \
			results/raw_predictions/improve/prime-2.0.csv \
		--output-dir results/analysis/improve/fixed --bootstrap 2000 --seed 20260820

hla-improve:
	PYTHONPATH=src $(PY) scripts/analyze_hla_sensitivity.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/mhcflurry-2.2.1.csv \
			results/raw_predictions/improve/bigmhc-v1.0.csv \
			results/raw_predictions/improve/prime-2.0.csv \
		--output results/analysis/improve/hla_sensitivity.csv \
		--per-hla-output results/analysis/improve/per_hla_metrics.csv \
		--permutations 2000 --seed 20260820

sensitivity-improve: evaluate-peptide-sensitivity evaluate-peptide-hla-rank-sensitivity \
	evaluate-exact-peptide-sensitivity evaluate-near-sensitivity evaluate-length-sensitivity

build-peptide-sensitivity:
	$(PY) scripts/build_peptide_sensitivity.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/mhcflurry-2.2.1.csv \
			results/raw_predictions/improve/bigmhc-v1.0.csv \
			results/raw_predictions/improve/prime-2.0.csv \
		--benchmark-output data/processed/improve_patient_peptide_sensitivity.csv \
		--prediction-dir results/raw_predictions/improve/peptide_sensitivity \
		--summary data/improve_patient_peptide_sensitivity_summary.json

evaluate-peptide-sensitivity: build-peptide-sensitivity
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/improve_patient_peptide_sensitivity.csv \
		--predictions results/raw_predictions/improve/peptide_sensitivity/*.csv \
		--output-dir results/analysis/improve/peptide_sensitivity \
		--bootstrap 2000 --seed 20260820

evaluate-peptide-hla-rank-sensitivity:
	$(PY) scripts/build_peptide_sensitivity.py \
		--benchmark data/processed/improve_benchmark.csv \
		--predictions results/raw_predictions/improve/mhcflurry-2.2.1.csv \
			results/raw_predictions/improve/bigmhc-v1.0.csv \
			results/raw_predictions/improve/prime-2.0.csv \
		--benchmark-output data/processed/improve_patient_peptide_hla_rank_sensitivity.csv \
		--prediction-dir results/raw_predictions/improve/peptide_sensitivity_hla_rank \
		--summary data/improve_patient_peptide_hla_rank_sensitivity_summary.json \
		--score-aggregation within-hla-percentile-max
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/processed/improve_patient_peptide_hla_rank_sensitivity.csv \
		--predictions results/raw_predictions/improve/peptide_sensitivity_hla_rank/*.csv \
		--output-dir results/analysis/improve/peptide_sensitivity_hla_rank \
		--bootstrap 2000 --seed 20260820

build-fixed-sensitivities:
	$(PY) scripts/build_fixed_sensitivity_subsets.py \
		--benchmark data/processed/improve_benchmark.csv \
		--audit research/training_overlap_audit_improve.csv \
		--predictions results/raw_predictions/improve/mhcflurry-2.2.1.csv \
			results/raw_predictions/improve/bigmhc-v1.0.csv \
			results/raw_predictions/improve/prime-2.0.csv \
		--output-root data/sensitivity \
		--summary data/improve_fixed_sensitivity_summary.json

evaluate-exact-peptide-sensitivity: build-fixed-sensitivities
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/sensitivity/exact_peptide_free/benchmark.csv \
		--predictions data/sensitivity/exact_peptide_free/predictions/*.csv \
		--output-dir results/analysis/improve/exact_peptide_free \
		--bootstrap 2000 --seed 20260820

evaluate-near-sensitivity: build-fixed-sensitivities
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/sensitivity/near_overlap_free/benchmark.csv \
		--predictions data/sensitivity/near_overlap_free/predictions/*.csv \
		--output-dir results/analysis/improve/near_overlap_free \
		--bootstrap 2000 --seed 20260820

evaluate-length-sensitivity: build-fixed-sensitivities
	PYTHONPATH=src $(PY) scripts/evaluate_benchmark.py \
		--benchmark data/sensitivity/length_9_10/benchmark.csv \
		--predictions data/sensitivity/length_9_10/predictions/*.csv \
		--output-dir results/analysis/improve/length_9_10 \
		--bootstrap 2000 --seed 20260820

figures: evaluate-improve baselines-improve hla-improve
	$(PY) scripts/generate_figures.py \
		--fixed results/analysis/improve/fixed/metrics.json \
		--lopo results/analysis/improve/baselines/lopo/metrics.json \
		--loso results/analysis/improve/baselines/loso/metrics.json \
		--hla results/analysis/improve/hla_sensitivity.csv

manuscript: figures sensitivity-improve
	$(PY) scripts/build_manuscript.py

manifest: manuscript validate-metrics
	$(PY) scripts/build_results_manifest.py

validate-metrics: evaluate-improve baselines-improve sensitivity-improve
	$(PY) scripts/validate_metrics.py

# Rebuild every analysis artifact from the versioned benchmark and raw predictions.
# The recursive invocation starts only after environment synchronization and inherits Make's jobserver.
reproduce-results: install
	$(MAKE) verify-reproduction

verify-reproduction: manifest
	$(MAKE) test

# Also download source data and install/run licensed third-party predictors.
full-reproduce: install
	$(MAKE) setup-predictors
	$(MAKE) download-improve
	$(MAKE) build-improve
	$(MAKE) predict-improve
	$(MAKE) verify-reproduction

test:
	uv run ruff check src scripts tests
	uv run pytest

validate-literature:
	uv run pytest -q tests/test_research_tables.py

status:
	uv run neorepro status

readme-i18n-status:
	$(PY) scripts/readme_i18n.py status

check-readme-i18n:
	$(PY) scripts/readme_i18n.py check
