.PHONY: docs

install:
	uv pip install -e .
	uv pip install polars pandas pytest ruff

docs:
	mkdocs serve

docs-deploy:
	mkdocs gh-deploy

clean:
	rm -rf .pytest_cache build dist scikit_lego.egg-info .ipynb_checkpoints .coverage* .mypy_cache .ruff_cache

lint:
	ruff format playtime tests
	ruff check playtime tests --fix

check: lint precommit test clean

pypi: clean
	uv build
	uv publish