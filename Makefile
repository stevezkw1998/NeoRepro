.PHONY: install test validate-literature status

install:
	python -m pip install '.[dev,analysis]'

test:
	ruff check src tests
	pytest

validate-literature:
	pytest -q tests/test_research_tables.py

status:
	neorepro status
