PYTHON = venv/bin/python
TEST_DIR = tests

.PHONY: all test unit_test perf_test coverage lint doc

all: test

test:
	$(PYTHON) -m pytest $(TEST_DIR)

unit_test:
	$(PYTHON) -m pytest $(TEST_DIR) -m "not perf"

perf_test:
	$(PYTHON) -m pytest $(TEST_DIR) -m "perf"

coverage:
	$(PYTHON) -m coverage run -m pytest $(TEST_DIR)
	$(PYTHON) -m coverage report

lint:
	ruff check triangulator.py

doc:
	pdoc3 triangulator --html --output-dir docs
