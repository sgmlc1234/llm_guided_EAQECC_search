PY ?= python3

.PHONY: reproduce deterministic test lint manifest manifest-check refutations figures clean

reproduce:            ## re-derive every claim (deterministic + external + search)
	$(PY) scripts/reproduce_eaqecc.py

deterministic:        ## the tier that needs only Python and NumPy
	$(PY) scripts/reproduce_eaqecc.py --tier deterministic

test:                 ## negative controls, evaluator, determinism
	$(PY) -m pytest

lint:
	ruff check scripts tests

manifest:             ## regenerate MANIFEST.sha256 after a legitimate archive change
	$(PY) scripts/make_manifest.py

manifest-check:
	$(PY) scripts/make_manifest.py --check

refutations:          ## rebuild CNF + DRAT for every registry entry lacking one (needs CaDiCaL)
	$(PY) scripts/refutations/run_registry.py

figures:              ## provenance map from the archived data
	$(PY) scripts/build_bound_map.py && $(PY) scripts/make_bound_map_figure.py --target both

clean:
	rm -rf artifacts/reproduce_eaqecc/reproduction_report.json figures .pytest_cache
	find . -name __pycache__ -type d -prune -exec rm -rf {} +
