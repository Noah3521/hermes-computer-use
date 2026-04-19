.PHONY: help install dev lint test smoke display-start display-stop display-status clean

PYTHON ?= python3

help:
	@echo "Targets:"
	@echo "  install         pip install ."
	@echo "  dev             pip install -e '.[dev,novnc]'"
	@echo "  lint            ruff check ."
	@echo "  test            pytest -m 'not e2e'"
	@echo "  smoke           run examples/smoke_test.py (needs Xvfb :99)"
	@echo "  display-start   bash scripts/display.sh start"
	@echo "  display-stop    bash scripts/display.sh stop"
	@echo "  display-status  bash scripts/display.sh status"
	@echo "  clean           remove build/cache artifacts"

install:
	$(PYTHON) -m pip install .

dev:
	$(PYTHON) -m pip install -e ".[dev,novnc]"

lint:
	ruff check .

test:
	pytest -m "not e2e"

smoke:
	$(PYTHON) examples/smoke_test.py

display-start:
	bash scripts/display.sh start

display-stop:
	bash scripts/display.sh stop

display-status:
	bash scripts/display.sh status

clean:
	rm -rf build dist *.egg-info .pytest_cache .ruff_cache __pycache__ src/**/__pycache__
