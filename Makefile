.PHONY: help setup install check lint test test-compat test-integration type-check security format \
	build clean firmware-setup firmware actions sync-agents check-agents
.DEFAULT_GOAL := help

PRE_COMMIT := uvx pre-commit@4.6.1

# The oldest Python the library supports (requires-python); development uses .python-version.
MIN_PYTHON := 3.13

# Unit tests only: integration tests need a board (docs/DEVELOPMENT.md).
UNIT := -m "unit and not integration and not slow"
COVERAGE := --cov=liveduino --cov-report=term-missing --cov-report=xml --cov-report=html \
	--cov-fail-under=100

# Path for type-check, security and format: DIR=path or a second goal (`make format tests`).
_qual_dir := $(or $(DIR),$(word 2,$(MAKECMDGOALS)),src tests)

# Pinned Arduino toolchain for the bundled firmware, shared verbatim with CI through
# `make firmware-setup`. Bump it here, then regenerate the firmware in CI.
ARDUINO_CORE      ?= arduino:avr@1.8.8
ARDUINO_LIBRARIES ?= Firmata@2.5.9 Servo@1.3.0 Ethernet@2.0.2

##@ General

help: ## Show this help
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z0-9_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Development

setup: ## Create the environment and install the git hooks (pre-commit + commit-msg); needs uv
	uv sync --locked
	$(PRE_COMMIT) install --install-hooks

install: ## Install the runtime dependencies only
	uv sync --locked --no-default-groups

check: lint test test-compat ## Everything to pass before finishing: hooks, then tests on 3.14 and 3.13

lint: ## Every hook in .pre-commit-config.yaml over the whole repo
	$(PRE_COMMIT) run --all-files --show-diff-on-failure

test: ## Unit tests with the 100% coverage gate on the development Python (.python-version)
	uv run pytest $(UNIT) $(COVERAGE) $(ARGS)

test-compat: ## Unit tests on Python 3.13, the oldest Python the library supports, in a throwaway env
	uv run --isolated --python $(MIN_PYTHON) --no-default-groups --group test pytest -q $(UNIT)

test-integration: ## Tests on a connected board (LIVEDUINO_PORT; LIVEDUINO_FLASH_PORT reflashes it)
	@test -n "$(LIVEDUINO_PORT)$(LIVEDUINO_FLASH_PORT)" || \
		{ echo "Set LIVEDUINO_PORT (or LIVEDUINO_FLASH_PORT), e.g. LIVEDUINO_PORT=/dev/ttyACM0"; exit 1; }
	uv run pytest -m integration $(ARGS)

type-check: ## mypy and Pyright on a path (default: src tests), a quick subset of lint
	uv run mypy $(_qual_dir)
	uv run pyright $(_qual_dir)

security: ## Bandit on a path (default: src tests), a quick subset of lint
	uv run bandit -c pyproject.toml -r $(_qual_dir)

format: ## Black, isort and ruff --fix on a path (default: src tests)
	uv run black $(_qual_dir)
	uv run isort $(_qual_dir)
	uv run ruff check --fix $(_qual_dir)

build: ## Build the sdist and wheel
	uv build

clean: ## Remove caches and build artifacts (keeps .venv)
	find . -type d -name __pycache__ -not -path './.venv/*' -prune -exec rm -rf {} +
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml dist

##@ Firmware

firmware-setup: ## Install arduino-cli (Homebrew) and the pinned core and libraries
	@command -v arduino-cli >/dev/null 2>&1 || command -v brew >/dev/null 2>&1 || \
		{ echo "Install arduino-cli: https://arduino.github.io/arduino-cli/latest/installation/"; exit 1; }
	@command -v arduino-cli >/dev/null 2>&1 || brew install arduino-cli
	arduino-cli core update-index
	arduino-cli core install $(ARDUINO_CORE)
	arduino-cli lib install $(ARDUINO_LIBRARIES)

firmware: ## Rebuild the bundled StandardFirmata images (needs firmware-setup; commit only Linux builds)
	uv run python scripts/build_firmware.py

##@ CI

# Goals after `actions`, prefixed so they never collide with real targets:
#   make actions ls | make actions workflow-<name> [branch-<branch>]   (or REF=<branch>)
_actions_args   := $(filter-out actions,$(MAKECMDGOALS))
_actions_sub    := $(firstword $(_actions_args))
_actions_name   := $(_actions_sub:workflow-%=%)
_actions_branch := $(patsubst branch-%,%,$(filter branch-%,$(_actions_args)))
_actions_ref    := $(or $(REF),$(_actions_branch),$(shell git rev-parse --abbrev-ref HEAD))

actions: ## List workflows (actions ls) or trigger one (actions workflow-<name> [branch-<branch>])
	@case '$(_actions_sub)' in \
	  ''|ls) \
	    for f in .github/workflows/*.yaml; do \
	      base=$$(basename "$$f" .yaml); \
	      desc=$$(grep -m1 '^name:' "$$f" | sed 's/^name:[[:space:]]*//'); \
	      printf '  \033[36m%-18s\033[0m %s\n' "$$base" "$$desc"; \
	    done ;; \
	  workflow-*) \
	    name='$(_actions_name:.yaml=)'; \
	    command -v gh >/dev/null 2>&1 || { echo 'gh CLI not found: https://cli.github.com/'; exit 1; }; \
	    test -f ".github/workflows/$$name.yaml" || { echo "No workflow '$$name' (make actions ls)"; exit 1; }; \
	    gh workflow run "$$name.yaml" --ref '$(_actions_ref)'; \
	    echo "Triggered $$name on $(_actions_ref); follow it with: gh run watch" ;; \
	  *) echo 'Usage: make actions ls | make actions workflow-<name> [branch-<branch>]'; exit 1 ;; \
	esac

##@ Agents

sync-agents: ## Regenerate agent pointers from .agents/
	uv run --no-project tooling/sync_agents.py

check-agents: ## Fail if agent pointers drifted from .agents/
	uv run --no-project tooling/sync_agents.py --check

# A second goal used as a path or a sub-command (`make format tests`, `make actions ls`) is not a
# target: do nothing for it.
%:
	@:
