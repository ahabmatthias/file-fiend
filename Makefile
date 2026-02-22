.PHONY: lint format test check

lint:
	ruff check app/ tests/
	mypy app/

format:
	ruff format app/ tests/

test:
	pytest tests/ -v --cov=app/core --cov-report=term-missing

check: lint test
