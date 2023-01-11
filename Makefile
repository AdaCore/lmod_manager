PYTEST = python3 -m pytest -vv
PYTHON_FILES := lmod_manager tests
BUILD_DIR := build
VERSION := $(shell python3 -c "import setuptools_scm; print(setuptools_scm.get_version())")
WHEEL := dist/lmod_manager-$(VERSION)-py3-none-any.whl

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

.PHONY: test test_lmod_manager test_installation

test: test_lmod_manager test_installation

test_lmod_manager:
	$(PYTEST) --cov=lmod_manager --cov-branch --cov-fail-under=100 --cov-report=term-missing:skip-covered tests

test_installation: $(BUILD_DIR)/venv/bin/lmod_manager
	$(BUILD_DIR)/venv/bin/lmod_manager --version

$(BUILD_DIR)/venv:
	python3 -m venv $(BUILD_DIR)/venv

$(BUILD_DIR)/venv/bin/lmod_manager: $(BUILD_DIR)/venv $(WHEEL)
	$(BUILD_DIR)/venv/bin/pip install --force-reinstall $(WHEEL)

.PHONY: install_devel

install_devel:
	$(MAKE) -C devutils install_devel
	python3 -m pip install -e ".[devel]"

.PHONY: dist

dist: $(WHEEL)

$(WHEEL): $(wildcard lmod_manager/*)
	python3 -m build

.PHONY: version

version:
	@echo $(VERSION)

clean:
	rm -rf .coverage .hypothesis .mypy_cache .pytest_cache $(BUILD_DIR)
