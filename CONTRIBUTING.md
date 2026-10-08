# Contributing to liveduino

Thanks for your interest in improving liveduino. This guide covers everything you need to
get a change merged.

By participating you agree to abide by the
[Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Getting started

1. Fork the repository.
2. Clone your fork: `git clone https://github.com/<your-user>/liveduino.git`
3. Set up the development environment. It needs [uv](https://docs.astral.sh/uv/), which installs
   Python 3.13 if it is missing:

   ```bash
   make setup              # uv sync --locked, then installs the git hooks (pre-commit, commit-msg)
   ```

## Development workflow

1. Create a branch from an up-to-date `main`: `feat/...`, `fix/...`, `docs/...` or `chore/...`.
2. Make your edits, with tests.
3. Run the full gate before pushing; the commit hook runs the same linters on staged files:

   ```bash
   make check          # every lint hook + 100% coverage gate
   ```

4. Push to your fork and open a pull request against `main`; fill the template, and under Test
   plan list only what you actually ran. The first time you contribute, a maintainer approves
   the CI run before it starts.

A few expectations:

- **Tests are required.** The suite enforces 100% coverage. New code needs unit tests under
  `tests/unit/`; hardware paths go under `tests/integration/` and stay skippable without a
  board connected.
- **Lint and types must be clean.** `make check` runs every hook in
  [`.pre-commit-config.yaml`](.pre-commit-config.yaml): Black, isort, Ruff, Flake8, Pylint,
  mypy, Pyright, Bandit, plus Markdown, YAML, JSON, spelling and workflow linters. CI runs the
  same linters through MegaLinter ([`docs/CI.md`](docs/CI.md)).
- **Coding standards live in [`.agents/rules/`](.agents/rules/).** They apply to humans too:
  public board methods are camelCase to match the Arduino API, do not use the em dash character,
  and prefer built-in generics over `typing` aliases.
- **Decisions are recorded.** A change that reverses or extends one comes with a new ADR in
  [`docs/adr/`](docs/adr/README.md).

See [`docs/DEVELOPMENT.md`](docs/DEVELOPMENT.md) for every `make` target and how to run the
hardware integration tests.

## Adding a board

Board profiles are auto-discovered: drop a file under
`src/liveduino/boards/catalog/` and it registers itself. See
[`docs/BOARDS.md`](docs/BOARDS.md) for the full walkthrough.

## Reporting bugs and requesting features

Use the [issue templates](https://github.com/adanmauri/liveduino/issues/new/choose). For
security issues, do not open a public issue: follow [`SECURITY.md`](SECURITY.md) instead.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/) with imperative subject lines
(for example `feat(boards): add the Arduino Mega profile`), one concern per commit. Do not credit
tools in commits or pull requests: the commit-msg hook rejects attribution trailers.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
