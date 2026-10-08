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

# Green OK.
define ECHO_OK
	@printf '\033[32m%s\033[0m\n' "$(1)"
endef

PRE_COMMIT := uvx pre-commit@4.6.1

.DEFAULT_GOAL := help
.PHONY: help install setup clean clean-cache clean-deps \
	test test-unit test-integration test-coverage \
	lint type-check security format check build firmware firmware-setup \
	sync-agents check-agents actions \
	src tests docs

##@ General

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Environment

install: ## Install the runtime dependencies only
	@echo "INFO: Installing production dependencies with UV..."
	@uv sync --locked --no-default-groups || (echo "ERROR: Failed to install dependencies" && exit 1)
	$(call ECHO_OK,OK: Installation complete.)

# pre-commit installs the Node.js and Go runtimes some hooks need, so the first run takes a while.
setup: ## Install the dev environment and the git hooks (pre-commit, commit-msg)
	@echo "INFO: Installing all dependencies (production + dev group) with UV..."
	@uv sync --locked || (echo "ERROR: Failed to install development dependencies" && exit 1)
	@echo "INFO: Installing git hooks (pre-commit, commit-msg)..."
	@$(PRE_COMMIT) install --install-hooks || (echo "ERROR: Failed to install git hooks" && exit 1)
	$(call ECHO_OK,OK: Setup complete. Run make firmware-setup too if you work on firmware.)

clean-cache: ## Remove build artifacts and caches (keeps .venv)
	@echo "INFO: Removing build artifacts and caches..."
	@find . -type d -name '__pycache__' -prune -exec rm -rf {} + 2>/dev/null || true
	@rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml dist
	$(call ECHO_OK,OK: Build artifacts and caches removed.)

clean-deps: ## Remove .venv and clear the uv cache
	@echo "INFO: Removing .venv and clearing uv cache..."
	@rm -rf .venv
	@-uv cache clean
	$(call ECHO_OK,OK: Dependencies cleaned.)

clean: clean-cache clean-deps ## clean-cache + clean-deps
	$(call ECHO_OK,OK: Environment at zero. Run make setup to reinstall.)

##@ Build

build: ## Build the sdist and wheel with uv
	@echo "INFO: Building liveduino wheel..."
	@uv build || (echo "ERROR: Build failed" && exit 1)
	$(call ECHO_OK,OK: Build complete.)

firmware-setup: ## Install the pinned arduino-cli core and libraries
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

firmware: ## Rebuild the bundled StandardFirmata images (needs firmware-setup)
	@echo "INFO: Building bundled StandardFirmata firmware (arduino-cli)..."
	@uv run python scripts/build_firmware.py || (echo "ERROR: Firmware build failed" && exit 1)
	$(call ECHO_OK,OK: Firmware built.)

##@ Testing

_pytest_cov_opts = --cov=liveduino --cov-report=html --cov-report=xml --cov-report=term-missing
_cov_flags = $(if $(COVERAGE),$(_pytest_cov_opts),)
_test_goals := test test-unit test-integration test-coverage

test-unit: ## Unit tests (COVERAGE=1 adds coverage, ARGS="..." goes to pytest)
	@echo "INFO: Running unit tests..."
	@uv run pytest $(_cov_flags) -m "unit and not integration and not slow" $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Unit tests failed" && exit 1)
	$(call ECHO_OK,OK: All unit tests passed.)

test-integration: ## Integration tests on a board (LIVEDUINO_PORT or LIVEDUINO_FLASH_PORT)
	@test -n "$(LIVEDUINO_PORT)$(LIVEDUINO_FLASH_PORT)" || (echo "ERROR: LIVEDUINO_PORT (or LIVEDUINO_FLASH_PORT) is required, e.g. LIVEDUINO_PORT=/dev/ttyACM0 make test-integration" && exit 1)
	@echo "INFO: Running integration tests on $(or $(LIVEDUINO_PORT),$(LIVEDUINO_FLASH_PORT))..."
	@LIVEDUINO_PORT=$(LIVEDUINO_PORT) uv run pytest $(_cov_flags) -m integration $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Integration tests failed" && exit 1)
	$(call ECHO_OK,OK: All integration tests passed.)

test: ## Every test, unit and integration (COVERAGE=1, ARGS="...")
	@echo "INFO: Running all tests..."
	@uv run pytest $(_cov_flags) $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Tests failed" && exit 1)
	$(call ECHO_OK,OK: All tests passed.)

test-coverage: ## Unit tests with the 100% coverage gate
	@echo "INFO: Running unit tests with coverage..."
	@uv run pytest $(_pytest_cov_opts) --cov-fail-under=100 -m "unit and not integration and not slow" $(or $(ARGS),$(filter-out $(_test_goals),$(MAKECMDGOALS))) || (echo "ERROR: Tests failed" && exit 1)
	$(call ECHO_OK,OK: All tests passed.)

##@ Code quality

# The full linter set lives in .pre-commit-config.yaml (docs/CI.md); type-check, security and
# format run single tools directly for a quick loop on a path.
lint: ## Every hook in .pre-commit-config.yaml over the whole repo
	@echo "INFO: Running every pre-commit hook on the whole repository..."
	@$(PRE_COMMIT) run --all-files --show-diff-on-failure || (echo "ERROR: Lint failed" && exit 1)
	$(call ECHO_OK,OK: Lint passed.)

type-check: ## mypy and Pyright on a path (default: src tests), a quick subset of lint
	@echo "INFO: Running type checking (mypy, pyright)..."
	@uv run mypy $(_qual_dir) || (echo "ERROR: mypy failed" && exit 1)
	@uv run pyright $(_qual_dir) || (echo "ERROR: pyright failed" && exit 1)
	$(call ECHO_OK,OK: Type checking passed.)

security: ## Bandit on a path (default: src tests), a quick subset of lint
	@echo "INFO: Running security scan (bandit)..."
	@uv run bandit -c pyproject.toml -r $(_qual_dir) || (echo "ERROR: Bandit failed" && exit 1)
	$(call ECHO_OK,OK: Security scan passed.)

format: ## Black, isort and ruff --fix on a path (default: src tests)
	@echo "INFO: Applying format fixes (black, isort, ruff --fix)..."
	@uv run black $(_qual_dir) || (echo "ERROR: Black failed" && exit 1)
	@uv run isort $(_qual_dir) || (echo "ERROR: Isort failed" && exit 1)
	@uv run ruff check --fix $(_qual_dir) || (echo "ERROR: Ruff check --fix failed" && exit 1)
	$(call ECHO_OK,OK: Format applied.)

# Definition of done (AGENTS.md). Recursive make so each sub-target sees a clean MAKECMDGOALS.
check: ## lint + test-coverage: the definition of done
	@$(MAKE) --no-print-directory lint
	@$(MAKE) --no-print-directory test-coverage
	$(call ECHO_OK,OK: All checks passed.)

##@ Agents

sync-agents: ## Regenerate agent pointers from .agents/
	@uv run --no-project tooling/sync_agents.py

check-agents: ## Fail if agent pointers drifted from .agents/
	@uv run --no-project tooling/sync_agents.py --check

##@ GitHub Actions

# Parsed from the goals after `actions` (the hyphen prefixes avoid colliding
# with real targets):
#   actions ls
#   actions workflow-<name> [branch-<branch>]
# REF=<branch> overrides the branch if you prefer a variable.
_actions_args   := $(filter-out actions,$(MAKECMDGOALS))
_actions_sub    := $(firstword $(_actions_args))
_actions_name   := $(_actions_sub:workflow-%=%)
_actions_branch := $(patsubst branch-%,%,$(filter branch-%,$(_actions_args)))
_actions_ref    := $(or $(REF),$(_actions_branch),$(shell git rev-parse --abbrev-ref HEAD))

actions: ## actions ls lists the workflows; actions workflow-<name> [branch-<branch>] runs one
	@case '$(_actions_sub)' in \
	  ''|ls) \
	    for f in .github/workflows/*.yaml; do \
	      base=$$(basename "$$f" .yaml); \
	      desc=$$(grep -m1 '^name:' "$$f" | sed 's/^name:[[:space:]]*//'); \
	      printf '  \033[36m%-14s\033[0m %s\n' "$$base" "$$desc"; \
	    done ;; \
	  workflow-*) \
	    name='$(_actions_name:.yaml=)'; \
	    command -v gh >/dev/null 2>&1 || { echo 'ERROR: gh CLI not found; install from https://cli.github.com/'; exit 1; }; \
	    test -f ".github/workflows/$$name.yaml" || { echo "ERROR: no workflow '$$name' (run: make actions ls)"; exit 1; }; \
	    gh workflow run "$$name.yaml" --ref '$(_actions_ref)'; \
	    printf '\033[32m%s\033[0m\n' "OK: Triggered $$name on $(_actions_ref). Follow it with: gh run watch" ;; \
	  *) echo 'Usage: make actions ls | make actions workflow-<name> [branch-<branch>]'; exit 1 ;; \
	esac

# Catch-all so a second goal used as a path (e.g. `make lint src`) is not built as a target.
.SILENT: src tests docs
%:
	@:
