.PHONY: install test smoke reproduce paper

install:
	python -m pip install -r requirements.txt
	python -m pip install -e . --no-deps

test:
	python -m pytest -q

smoke:
	python scripts/reproduce_all.py --samples 8

reproduce:
	python scripts/reproduce_all.py --samples 128

paper:
	python scripts/reproduce_all.py --samples 128 --compile
