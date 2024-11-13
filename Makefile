.PHONY: docs

install:
	python -m pip install -e .
	python -m pip install polars pandas pytest ruff

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
	python setup.py sdist
	python setup.py bdist_wheel --universal
	twine upload dist/*
