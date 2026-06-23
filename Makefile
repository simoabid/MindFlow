.PHONY: help install dev lint format typecheck test cov check doctor clean

help:
	@echo "MindFlow developer tasks:"
	@echo "  make dev        Install the package with dev dependencies (editable)"
	@echo "  make lint       Run ruff linter"
	@echo "  make format     Auto-format the code with ruff"
	@echo "  make typecheck  Run mypy"
	@echo "  make test       Run the unit test suite"
	@echo "  make cov        Run tests with a coverage report"
	@echo "  make check      Run lint, typecheck and tests (what CI runs)"
	@echo "  make doctor     Run the MindFlow environment diagnostics"

dev:
	pip install -e ".[dev]"

install:
	pip install -e .

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

typecheck:
	mypy mindflow

test:
	pytest -m "not integration"

cov:
	pytest -m "not integration" --cov=mindflow --cov-report=term-missing

check: lint typecheck test

doctor:
	python -m mindflow.cli doctor

clean:
	rm -rf build dist *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
