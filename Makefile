# Liveduino - Makefile
# Python library for live Arduino/Wiring commands. Targets wrap UV + project tooling.

# Quality/test target directory. Override with DIR=path or as the second goal
# (e.g. `make lint src`). Defaults to the source and tests directories.
_qual_dir := $(or $(DIR),$(word 2,$(MAKECMDGOALS)),src tests)

# Integration tests require a connected Arduino serial port.
LIVEDUINO_PORT ?=

# Pinned Arduino toolchain for reproducible bundled firmware. These exact
# versions are the single source of truth: CI consumes them through
# `make firmware-setup`, so local builds and CI produce byte-identical hex.
# Bump them here (and regenerate firmware) when you intend to update.
ARDUINO_CORE      ?= arduino:avr@1.8.8
ARDUINO_LIBRARIES ?= Firmata@2.5.9 Servo@1.3.0 Ethernet@2.0.2

# Green OK / cyan section titles.
define ECHO_OK
	@printf '\033[32m%s\033[0m\n' "$(1)"
endef
define ECHO_TITLE
	@printf '\033[36m%s\033[0m\n' "$(1)"
endef

.PHONY: help install install-dev clean clean-cache clean-deps \
	test test-unit test-integration test-coverage \
	lint type-check security quality format format-quality check pre-commit build firmware firmware-setup \
	actions action \
	src tests docs

# Default target
help:
	@echo ""
	$(call ECHO_TITLE,Liveduino - Development Commands)
	@echo "======================================"
	@echo ""
	$(call ECHO_TITLE,[ENV] Environment & Dependencies:)
	@echo "  install                 - Install production dependencies only"
	@echo "  install-dev             - Install all dependencies (incl. dev) + pre-commit hooks"
	@echo "  clean-cache             - Remove build artifacts and caches (keeps .venv)"
	@echo "  clean-deps              - Remove .venv and clear uv cache"
	@echo "  clean                   - clean-cache + clean-deps"
	@echo ""
	$(call ECHO_TITLE,[BUILD] Package:)
	@echo "  build                   - Build wheel with uv"
	@echo "  firmware-setup          - Install pinned arduino-cli core + libraries"
	@echo "  firmware                - Rebuild bundled StandardFirmata hex (needs firmware-setup)"
	@echo ""
	$(call ECHO_TITLE,[CI] GitHub Actions \(via gh\):)
	@echo "  actions                 - List the repository workflows"
	@echo "  action WF=<name>        - Trigger a workflow run (e.g. make action WF=tests)"
	@echo "                            Optional: REF=<branch> (defaults to current branch)"
	@echo ""
	$(call ECHO_TITLE,[TEST] Testing:)
	@echo "  test                    - Run all tests (unit + integration)"
	@echo "  test-unit               - Run unit tests only"
	@echo "  test-integration        - Run integration tests (requires LIVEDUINO_PORT)"
	@echo "  test-coverage           - Unit tests with coverage (100% gate on liveduino)"
	@echo ""
	@echo "  Usage:          make test COVERAGE=1   ARGS=\"...\" for pytest"
	@echo "  Examples:       make test-unit COVERAGE=1"
	@echo "                  LIVEDUINO_PORT=/dev/ttyACM0 make test-integration"
	@echo ""
	$(call ECHO_TITLE,[QUALITY] Code Quality:)
	@echo "  lint                    - ruff, flake8, pylint"
	@echo "  type-check              - mypy, pyright"
	@echo "  security                - bandit"
	@echo "  quality                 - lint + type-check + security"
	@echo "  format                  - black, isort, ruff --fix"
	@echo "  format-quality          - format then quality"
	@echo "  check                   - lint + type-check + test-coverage (pre-finish gate)"
	@echo "  pre-commit              - run all pre-commit hooks on the repo"
	@echo ""
	@echo "  Usage:          make <target> [path] or DIR=path (default: src tests)"
	@echo "  Examples:       make lint src   make type-check tests"
	@echo ""

# --- Environment & dependencies ---

install:
	@echo "INFO: Installing production dependencies with UV..."
	@uv sync --no-group dev || (echo "ERROR: Failed to install dependencies" && exit 1)
	$(call ECHO_OK,OK: Installation complete.)

install-dev:
	@echo "INFO: Installing all dependencies (production + development) with UV..."
	@uv sync --group dev || (echo "ERROR: Failed to install development dependencies" && exit 1)
	@echo "INFO: Installing pre-commit hooks (commit + pre-push)..."
	@uv run pre-commit install
	@uv run pre-commit install --hook-type pre-push
	@$(MAKE) --no-print-directory firmware-setup
	$(call ECHO_OK,OK: Installation complete.)

clean-cache:
	@echo "INFO: Removing build artifacts and caches..."
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml dist
	$(call ECHO_OK,OK: Build artifacts and caches removed.)

clean-deps:
	@echo "INFO: Removing .venv and clearing uv cache..."
	@rm -rf .venv
	@-uv cache clean
	$(call ECHO_OK,OK: Dependencies cleaned.)

clean: clean-cache clean-deps
	$(call ECHO_OK,OK: Environment at zero. Run make install-dev to reinstall.)

# --- Build ---

build:
	@echo "INFO: Building liveduino wheel..."
	@uv build || (echo "ERROR: Build failed" && exit 1)
	$(call ECHO_OK,OK: Build complete.)

firmware-setup:
	@echo "INFO: Setting up Arduino firmware toolchain..."
	@command -v arduino-cli >/dev/null 2>&1 || { \
		echo "INFO: arduino-cli not found on PATH; attempting to install it..."; \
		if command -v brew >/dev/null 2>&1; then \
			brew install arduino-cli; \
		else \
			echo "ERROR: arduino-cli is required. Install it from"; \
			echo "       https://arduino.github.io/arduino-cli/latest/installation/ and re-run."; \
			exit 1; \
		fi; \
	}
	@echo "INFO: Installing pinned core ($(ARDUINO_CORE)) and libraries ($(ARDUINO_LIBRARIES))..."
	@arduino-cli core update-index
	@arduino-cli core install $(ARDUINO_CORE)
	@arduino-cli lib install $(ARDUINO_LIBRARIES)
	$(call ECHO_OK,OK: Firmware toolchain ready.)

firmware:
	@echo "INFO: Building bundled StandardFirmata firmware (arduino-cli)..."
	@uv run python scripts/build_firmware.py || (echo "ERROR: Firmware build failed" && exit 1)
	$(call ECHO_OK,OK: Firmware built.)

# --- Testing ---

_pytest_cov_opts = --cov=liveduino --cov-report=html --cov-report=term-missing
_cov_flags = $(if $(COVERAGE),$(_pytest_cov_opts),)
_test_goals := test test-unit test-integration test-coverage

test-unit:
	@echo "INFO: Running unit tests..."
	@uv run pytest $(_cov_flags) -m "unit and not integration and not slow" $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Unit tests failed" && exit 1)
	$(call ECHO_OK,OK: All unit tests passed.)

test-integration:
	@test -n "$(LIVEDUINO_PORT)" || (echo "ERROR: LIVEDUINO_PORT is required, e.g. LIVEDUINO_PORT=/dev/ttyACM0 make test-integration" && exit 1)
	@echo "INFO: Running integration tests on $(LIVEDUINO_PORT)..."
	@LIVEDUINO_PORT=$(LIVEDUINO_PORT) uv run pytest $(_cov_flags) -m integration $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Integration tests failed" && exit 1)
	$(call ECHO_OK,OK: All integration tests passed.)

test:
	@echo "INFO: Running all tests..."
	@uv run pytest $(_cov_flags) $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Tests failed" && exit 1)
	$(call ECHO_OK,OK: All tests passed.)

test-coverage:
	@echo "INFO: Running unit tests with coverage..."
	@uv run pytest $(_pytest_cov_opts) --cov-fail-under=100 -m "unit and not integration and not slow" $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Tests failed" && exit 1)
	$(call ECHO_OK,OK: All tests passed.)

# --- Code quality ---

lint:
	@echo "INFO: Running linters (ruff, flake8, pylint)..."
	@uv run ruff check $(_qual_dir) || (echo "ERROR: Ruff check failed" && exit 1)
	@uv run flake8 $(_qual_dir) || (echo "ERROR: Flake8 check failed" && exit 1)
	@uv run pylint $(_qual_dir) || (echo "ERROR: Pylint check failed" && exit 1)
	$(call ECHO_OK,OK: Lint passed.)

type-check:
	@echo "INFO: Running type checking (mypy, pyright)..."
	@uv run mypy $(_qual_dir) || (echo "ERROR: mypy failed" && exit 1)
	@uv run pyright $(_qual_dir) || (echo "ERROR: pyright failed" && exit 1)
	$(call ECHO_OK,OK: Type checking passed.)

security:
	@echo "INFO: Running security scan (bandit)..."
	@uv run bandit -c pyproject.toml -r $(_qual_dir) || (echo "ERROR: Bandit failed" && exit 1)
	$(call ECHO_OK,OK: Security scan passed.)

quality: lint type-check security
	$(call ECHO_OK,OK: Quality passed.)

format:
	@echo "INFO: Applying format fixes (black, isort, ruff --fix)..."
	@uv run black $(_qual_dir) || (echo "ERROR: Black failed" && exit 1)
	@uv run isort $(_qual_dir) || (echo "ERROR: Isort failed" && exit 1)
	@uv run ruff check --fix $(_qual_dir) || (echo "ERROR: Ruff check --fix failed" && exit 1)
	$(call ECHO_OK,OK: Format applied.)

format-quality: format quality
	$(call ECHO_OK,OK: Format and quality passed.)

# Full local gate to run before finishing a task (matches AGENTS.md).
# Uses recursive make so each sub-target sees a clean MAKECMDGOALS.
check:
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory type-check
	@$(MAKE) --no-print-directory test-coverage
	$(call ECHO_OK,OK: All checks passed.)

pre-commit:
	@echo "INFO: Running pre-commit hooks on all files..."
	@uv run pre-commit run --all-files || (echo "ERROR: pre-commit hooks failed" && exit 1)
	$(call ECHO_OK,OK: pre-commit hooks passed.)

# --- GitHub Actions (via the gh CLI) ---

actions:
	@command -v gh >/dev/null 2>&1 || (echo "ERROR: gh CLI not found; install from https://cli.github.com/" && exit 1)
	@gh workflow list --all

# Trigger any workflow. WF=<name> (with or without .yaml), optional REF=<branch>.
# Example: make action WF=firmware    make action WF=tests REF=main
action:
	@command -v gh >/dev/null 2>&1 || (echo "ERROR: gh CLI not found; install from https://cli.github.com/" && exit 1)
	@test -n "$(WF)" || (echo "ERROR: set WF=<workflow>, e.g. make action WF=firmware (list: make actions)" && exit 1)
	@gh workflow run "$(WF:.yaml=).yaml" --ref "$(or $(REF),$(shell git rev-parse --abbrev-ref HEAD))"
	$(call ECHO_OK,OK: Triggered $(WF:.yaml=). Follow it with: gh run watch)

# Catch-all so a second goal used as a path (e.g. `make lint src`) is not built as a target.
.SILENT: src tests docs
%:
	@:
