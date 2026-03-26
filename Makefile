PYTHON     := .venv/bin/python3
PYTEST     := .venv/bin/pytest
PANELMARK  := $(abspath ../panelmark)
PYTHONPATH := $(abspath .):$(PANELMARK)

export PYTHONPATH

.PHONY: test test-all run-hello run-task-manager

## Run tests for panelmark-tui only (no cross-repo PYTHONPATH needed beyond .venv install)
test:
	$(PYTEST) -q

## Run the full test suite with the explicit PYTHONPATH (required when panelmark is not installed)
test-all:
	PYTHONPATH=$(PYTHONPATH) $(PYTEST) -q

## Launch the hello.py example
run-hello:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) examples/hello.py

## Launch the task_manager.py example
run-task-manager:
	PYTHONPATH=$(PYTHONPATH) $(PYTHON) examples/task_manager.py
