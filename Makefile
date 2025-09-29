.PHONY: docs

install:
	python -m pip install -e .
	python -m pip install polars pandas pytest ruff

docs:
	marimo edit docs.py

docs-serve:
	marimo run docs.py

docs-build:
	marimo export html-wasm docs.py -o docs/index.html
	@echo "WASM export complete. Documentation available at docs/index.html"

docs-deploy:
	make docs-build
	@echo "Documentation built for deployment. Commit and push to deploy via GitHub Pages."

clean:
	rm -rf .pytest_cache build dist scikit_lego.egg-info .ipynb_checkpoints .coverage* .mypy_cache .ruff_cache

lint:
	ruff format skplay tests
	ruff check skplay tests --fix

check: lint precommit test clean

pypi: clean
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
