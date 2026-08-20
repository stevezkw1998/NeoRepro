.PHONY: install test validate-literature evaluate status

install:
	python -m pip install '.[dev,analysis]'

test:
	ruff check src tests
	pytest

validate-literature:
	pytest -q tests/test_research_tables.py

evaluate:
	python scripts/evaluate_benchmark.py \
		--benchmark data/processed/benchmark.csv \
		--predictions results/raw_predictions/mhcflurry-2.2.1.csv \
			results/raw_predictions/bigmhc-v1.0.csv \
			results/raw_predictions/prime-2.0.csv \
		--output-dir results/analysis --bootstrap 2000 --seed 20260820

status:
	neorepro status
