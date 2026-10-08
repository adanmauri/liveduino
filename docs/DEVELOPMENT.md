# Development

How to set up, check and change this repository. What the library does is in the
[README](../README.md), how it works inside in [ARCHITECTURE.md](ARCHITECTURE.md), and what checks a
change, locally and in CI, in [CI.md](CI.md).

## Setup

Needs [uv](https://docs.astral.sh/uv/) and `git`. uv installs Python 3.13 (from
`.python-version`) when it is missing, and pre-commit, which runs through `uvx`, installs the
Node.js and Go runtimes some hooks need (the first `make setup` takes a few minutes for that).

```bash
make setup            # uv sync --locked, then installs the pre-commit and commit-msg hooks
make check            # everything that must pass before a change is done
make firmware-setup   # only when you work on the bundled firmware (arduino-cli toolchain)
```

`make setup` creates `.venv` with the `dev` dependency group (`test` + `lint`).

## Commands

`make` with no target prints this list, grouped.

| Target                                             | What it does                                                                                    |
|----------------------------------------------------|-------------------------------------------------------------------------------------------------|
| `make setup`                                       | Install the dev environment and the git hooks (pre-commit, commit-msg)                          |
| `make install`                                     | Install the runtime dependencies only                                                           |
| `make check`                                       | `lint`, then `test-coverage`: the definition of done                                            |
| `make lint`                                        | Every hook in [`.pre-commit-config.yaml`](../.pre-commit-config.yaml) over the whole repository |
| `make type-check`                                  | mypy and Pyright only, on a path (`make type-check src`): a quick subset of `lint`              |
| `make security`                                    | Bandit only, on a path: a quick subset of `lint`                                                |
| `make format`                                      | Black, isort, `ruff --fix` on a path                                                            |
| `make test-coverage`                               | Unit tests with the 100% coverage gate                                                          |
| `make test-unit` / `make test`                     | Unit tests / every test (`COVERAGE=1` adds coverage, `ARGS="..."` goes to pytest)               |
| `make test-integration`                            | Integration tests (`LIVEDUINO_PORT`, or `LIVEDUINO_FLASH_PORT` to reflash)                      |
| `make build`                                       | Build the sdist and wheel                                                                       |
| `make firmware-setup`                              | Install the pinned arduino-cli core + libraries                                                 |
| `make firmware`                                    | Rebuild the bundled StandardFirmata hex (needs `firmware-setup`)                                |
| `make sync-agents` / `make check-agents`           | Regenerate / verify the agent pointers from `.agents/`                                          |
| `make actions ls` / `make actions workflow-<name>` | List / trigger a GitHub Actions workflow via `gh`                                               |

## Conventions

The binding checklists are [`.agents/rules/coding-standards.md`](../.agents/rules/coding-standards.md)
and [`.agents/rules/library-guardrails.md`](../.agents/rules/library-guardrails.md), for people
and agents alike. The short version:

- **Language:** code, comments, docs, commit messages and user-facing text in English; no em dash.
- **Python:** 3.13+; built-in generics and `X | None`; type hints everywhere; the docstring format
  in the coding standards.
- **Arduino fidelity:** camelCase board methods with Arduino's names and semantics.
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)
  (`feat(boards): ...`, `fix(protocols): ...`), one concern per commit, no tool attribution.
- **Branches:** `feat/...`, `fix/...`, `docs/...`, `chore/...` from an up-to-date `main`.
- **Pull requests:** fill [the template](../.github/PULL_REQUEST_TEMPLATE.md); the test plan lists
  only what was actually run.
- **Decisions:** a change that reverses or extends one comes with a new [ADR](adr/README.md).

## Dependencies

uv manages the interpreter, the environment, the lock and every command; never `pip`.

- Runtime dependencies (`pyserial`) declare compatible ranges; adding one needs approval.
- Development tools are in the `test` and `lint` groups of `pyproject.toml`, unpinned there and
  pinned in `uv.lock`, which is committed. Add one with `uv add --group <test|lint> <package>`.
  CI installs only the group a job needs, with `--locked`.
- pre-commit is not a dependency: the `Makefile` runs it with `uvx`, pinned in `PRE_COMMIT`.
- Dependabot opens monthly updates for `uv.lock` and the actions, for releases at least 14 days
  old. Pick the same age when bumping anything by hand.
- The pre-commit hooks outside uv pin the MegaLinter image's versions; how to bump them is in
  [CI.md](CI.md#same-settings-and-mostly-the-same-versions).

## Agent assets

AI agents follow [`AGENTS.md`](../AGENTS.md), the one canonical instructions file; `CLAUDE.md` and
`.github/copilot-instructions.md` only point to it. Rules (`.agents/rules/`) and skills
(`.agents/skills/`) live once, in [`.agents/`](../.agents/README.md), and
`tooling/sync_agents.py` writes a thin pointer for each tool in `.claude/skills/`,
`.github/skills/`, `.github/instructions/` and `.cursor/rules/`. Pointers are generated and
committed: edit the file in `.agents/`, then run `make sync-agents`; `make check` fails when they
drift. No tool is credited in commits, pull requests or docs, and a commit-msg hook rejects
attribution lines.

## Integration tests

They need a real board and skip without one:

```bash
LIVEDUINO_PORT=/dev/ttyACM0 make test-integration
```

The flashing integration test is destructive (it overwrites the board's firmware)
and is gated by its own variable, so the runtime tests above never reflash by
accident. Set `LIVEDUINO_FLASH_PORT` (and optionally `LIVEDUINO_FLASH_BOARD`,
default `arduino:uno`) to flash the bundled StandardFirmata and confirm the board
answers Firmata afterwards:

```bash
LIVEDUINO_FLASH_PORT=/dev/ttyACM0 make test-integration
```

## Bundled firmware

The firmware images shipped under `src/liveduino/firmware/` (used by `liveduino
flash`) are generated, not hand-written. `make firmware` runs
`scripts/build_firmware.py`, which reads each catalog board's `fqbn`,
`firmware_sketch` (the primary serial image), and `firmware_sketches` (extra
Firmata variants, e.g. `StandardFirmataEthernet`) metadata, compiles each with
`arduino-cli`, and writes one image per built sketch (named after the board model,
e.g. `standardfirmata-uno.hex`, `standardfirmataethernet-ethernet.hex`) plus
`manifest.json`. Anything that does not build is recorded under `unsupported`
instead of failing: the primary image only when it does not fit on the board, and
extra variants whenever they need an uninstalled library or
per-deployment config (`StandardFirmataEthernet` needs the `Ethernet` library;
`StandardFirmataWiFi` needs a configured `wifiConfig.h`).

`make firmware-setup` installs the **pinned** toolchain the build expects
(`arduino:avr` core plus the `Firmata`, `Servo`, and `Ethernet` libraries; exact
versions live in the `Makefile`, shared verbatim with CI). It also installs
`arduino-cli` itself via Homebrew if missing:

```bash
make firmware-setup
make firmware
```

**Important: firmware is a CI/Linux artifact.** The bundled `.hex` are not
byte-reproducible across operating systems: the `avr-gcc` in the `arduino:avr`
core differs between macOS and Linux, so a macOS build will not match the
Linux build CI verifies against, even with identical pinned versions. So the
committed images must come from Linux. Do **not** commit locally-built firmware;
regenerate it in CI instead:

```bash
make actions workflow-firmware   # runs the Firmware workflow (workflow_dispatch)
```

The `regenerate` job compiles on Linux and pushes a `firmware/rebuild` branch (it
opens a PR too if the repo allows Actions to create PRs). The `verify` job fails a
push/PR whose bundled firmware is out of date.

## Releasing

A release publishes to PyPI: `publish.yaml` builds and uploads the package when a GitHub release
is published. The repository has immutable releases turned on, so once published a `vX.Y.Z` tag
can never move or be deleted, and PyPI never accepts the same version twice: a release is final.
Agents prepare the notes and the commands; a person runs them (`.claude/settings.json` does not
let agents create tags or releases).

1. Bump `version` in `pyproject.toml` and add the release to `CHANGELOG.md`, in a pull request.
   Merge it and wait for the workflows on `main` to pass.
2. Write the notes: how to install or upgrade, what changes for users (Arduino API, boards,
   connections, CLI), requirements (Python, firmware), known limits, any breaking change, and the
   changelog entry.
3. Create a draft pinned to the merged commit; a draft creates its tag only when published:
   `gh release create vX.Y.Z --draft --title vX.Y.Z --target <sha> --notes-file <notes>`.
4. Review the draft on GitHub and publish it. `publish.yaml` uploads to PyPI; check that the run
   passes and that the new version installs: `uvx --from liveduino==X.Y.Z liveduino-cli boards`.

A breaking change to the public API bumps the minor version while liveduino is `0.x`, and the
major version from `1.0.0` on.
