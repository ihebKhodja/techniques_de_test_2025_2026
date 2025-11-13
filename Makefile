PYTHON=venv\Scripts\python.exe
TEST_DIR=tests

all: test

test:
	$(PYTHON) -m pytest $(TEST_DIR)

unit_test:
	$(PYTHON) -m pytest $(TEST_DIR) -m "not perf"

perf_test:
	$(PYTHON) -m pytest $(TEST_DIR) -m "perf"

coverage:
	$(PYTHON) -m coverage run -m pytest $(TEST_DIR)
	$(PYTHON) -m coverage report -m

lint:
	ruff check triangulator

doc:
	pdoc3 triangulator --html --output-dir docs