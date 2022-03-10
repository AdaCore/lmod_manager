VERBOSE ?= @
TEST_PROCS ?= $(shell nproc)
PYTEST = python3 -m pytest -n$(TEST_PROCS) -vv
PYTHON_FILES := lmod_manager

.PHONY: all check check_black check_isort check_flake8 check_pylint check_mypy check_doc format \
	test install_devel clean

all: check test

check: check_black check_isort check_flake8 check_pylint check_mypy check_pydocstyle

check_black:
	black --check --diff $(PYTHON_FILES)

check_isort:
	isort --check --diff $(PYTHON_FILES)

check_flake8:
	pflake8 $(PYTHON_FILES)

check_pylint:
	pylint $(PYTHON_FILES)

check_mypy:
	mypy --pretty $(PYTHON_FILES)

check_pydocstyle:
	pydocstyle $(PYTHON_FILES)

format:
	black $(PYTHON_FILES)
	isort $(PYTHON_FILES)

test:
	$(PYTEST) tests

install_devel:
	$(MAKE) -C .config/python-style install_devel

clean:
	rm -rf .coverage .hypothesis .mypy_cache .pytest_cache
