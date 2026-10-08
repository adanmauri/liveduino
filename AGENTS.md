# Liveduino: agent operating guidelines

Canonical, vendor-neutral instructions for AI agents working in this repo
([agents.md](https://agents.md/) standard). `CLAUDE.md` and `.github/copilot-instructions.md` are
thin pointers here.

## What this repo is

**Liveduino** is a Python 3.13 library that controls microcontrollers from the host with the
**Arduino/Wiring API** (`pinMode`, `digitalWrite`, `analogRead`, ...). It is the successor of
[Frameduino](https://github.com/adanmauri/frameduino), published on PyPI as **`liveduino`**.

- **Today:** Arduino boards running **StandardFirmata**, driven by a native `FirmataProtocol` (the
  Firmata 2.x wire protocol, implemented in-house over a `Driver`). USB serial, TCP/WiFi or
  Bluetooth RFCOMM by swapping the driver.
- **Goal:** zero learning curve for Arduino users: same function names and semantics, in Python.
- **Not in scope:** running Python on the MCU, compiling sketches, or exposing Firmata wire
  details to users.

## Read before working

| Concern                                                      | Source                                                                       |
|--------------------------------------------------------------|------------------------------------------------------------------------------|
| What the library does, quick start                           | [`README.md`](README.md)                                                     |
| Public API, boards, connections, CLI                         | [`docs/`](docs/README.md)                                                    |
| How it works inside: layers, data flow, drivers              | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)                               |
| Setup, commands, tests, firmware build                       | [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md)                                 |
| Which check runs where, CI workflows, linter versions        | [`docs/CI.md`](docs/CI.md)                                                   |
| Decisions and their rationale                                | [`docs/adr/`](docs/adr/README.md)                                            |
| Hard constraints: Arduino fidelity, layers, boards, hardware | [`.agents/rules/library-guardrails.md`](.agents/rules/library-guardrails.md) |
| Code style, docstrings, tests, dependencies                  | [`.agents/rules/coding-standards.md`](.agents/rules/coding-standards.md)     |
| Flashing StandardFirmata onto a board                        | [`firmware/README.md`](firmware/README.md)                                   |
| Pending work                                                 | [`TODO.md`](TODO.md)                                                         |
| How agent assets are organized                               | [`.agents/README.md`](.agents/README.md)                                     |

## Layout

```text
src/liveduino/
  constants.py, types.py    Arduino constants (HIGH, INPUT, A0...) and Literal types
  utilities.py              host value helpers (map_range, constrain)
  boards/                   Board base class, registry, and catalog/ (one Board subclass per file)
  protocols/                native FirmataProtocol
  drivers/                  SerialDriver, TcpDriver, BluetoothDriver (SocketDriver base)
  programmers/              bootloader flashers (STK500v1), Intel HEX, firmware resolver
  firmware/                 bundled StandardFirmata images + manifest.json (generated)
  cli.py                    liveduino-cli: flash, boards, ports
  connection.py             connect("arduino:uno", port)
scripts/                    build_firmware.py, render_pypi_readme.py (shipped tooling)
firmware/                   MCU setup docs
tests/unit/                 mocks, @pytest.mark.unit, 100% coverage gate
tests/integration/          real hardware, @pytest.mark.integration, LIVEDUINO_PORT
tooling/                    repo scripts (agent pointer sync, docs and commit-msg checks), not shipped
```

## Workflow

0. **Once per clone:** `make setup` installs the environment and the git hooks (pre-commit and
   commit-msg). Needs `uv`. `make firmware-setup` adds the Arduino toolchain when you touch
   firmware.
1. **Branch** from an up-to-date `main` with `create-branch`: `feat/...`, `fix/...`, `docs/...`,
   `chore/...`.
2. **Commit** with `create-commit` (Conventional Commits, no tool attribution).
3. **Open the PR** with `write-pr` (body) and `make-pr` (mechanics).
4. **File issues** with `write-issue`.
5. **Record decisions:** a change that reverses or extends an ADR comes with a new one, from
   [`docs/adr/template.md`](docs/adr/template.md); rules cite the ADR instead of repeating it.

## Before you finish

- `make check` passes: every hook in [`.pre-commit-config.yaml`](.pre-commit-config.yaml) over the
  whole repo, then the unit tests with the 100% coverage gate.
- `make build` passes when packaging, `pyproject.toml` or `src/liveduino/firmware/` changed.
- New code has unit tests; hardware paths have integration tests that skip without a board.
- README, `docs/`, `firmware/*/README.md` and this file agree with the change.
- CI also runs the scanners that have no local hook (vulnerabilities, verified secrets, links,
  JSON schemas) through MegaLinter (`.github/workflows/code-quality.yaml`); check its result on
  the pull request.
- Summarize the changes and any residual risks.

## Verification on hardware

Unit tests cover the protocol, drivers and boards against mocks. They cannot prove a board
**responds**. When a change touches hardware behavior:

1. Run `LIVEDUINO_PORT=/dev/ttyACM0 make test-integration` with a board connected, or ask the
   user to run it. Do not report hardware behavior as verified without that run.
2. Flashing is destructive: `LIVEDUINO_FLASH_PORT` reflashes the board. Ask before setting it.

## Boundaries

- Never push to `main`, force-push, or rewrite shared history unless the user asks for it.
- Never create tags or GitHub releases: a person does, because a release publishes to PyPI and
  cannot be undone. Prepare the notes and the commands ([`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md#releasing)).
- Never add a runtime dependency without approval (see the guardrails).
- Never break the public API or Arduino/Wiring fidelity.
- Never bypass the hooks (`--no-verify`) or weaken a check to make it pass.
- Never commit firmware built on macOS (see the guardrails).
- Never attribute work to an AI tool in commits, PRs, issues, docs or comments (see
  `create-commit`).
- Never expose secrets or credentials; configuration comes from environment variables.
- Edit agent assets only under `.agents/`, then run `make sync-agents`; never edit the generated
  pointers in `.claude/skills/`, `.github/skills/`, `.github/instructions/` or `.cursor/rules/`.

## Skills

| Skill           | Use it to                                                 |
|-----------------|-----------------------------------------------------------|
| `create-branch` | Start a branch from an up-to-date `main`                  |
| `create-commit` | Commit a scoped change with a Conventional Commit message |
| `write-pr`      | Fill the PR template into `pr-body.tmp`                   |
| `make-pr`       | Push and open the PR against `main`                       |
| `write-issue`   | File or update a GitHub issue with hardware context       |
