# Contributing to liveduino

Thanks for your interest in improving liveduino. This guide covers everything you need to
get a change merged.

By participating you agree to abide by the
[Code of Conduct](.github/CODE_OF_CONDUCT.md).

## Getting started

liveduino requires **Python 3.13+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/adanmauri/liveduino.git
cd liveduino
uv python pin 3.13
uv sync --all-groups
make install-dev        # installs dev deps + pre-commit hooks
```

## Development workflow

1. Create a branch off `main` for your change.
2. Make your edits, with tests.
3. Run the full gate before pushing:

   ```bash
   make check          # lint + type-check + 100% coverage gate
   ```

4. Open a pull request against `main`.

A few expectations:

- **Tests are required.** The suite enforces 100% coverage. New code needs unit tests under
  `tests/unit/`; hardware paths go under `tests/integration/` and stay skippable without a
  board connected.
- **Lint and types must be clean.** `make check` runs ruff, flake8, pylint, mypy, pyright,
  and bandit. The pre-commit hooks run the same checks on commit.
- **Coding standards live in [`AGENTS.md`](AGENTS.md).** It applies to humans too: public
  board methods are camelCase to match the Arduino API, do not use the em dash character,
  and prefer built-in generics over `typing` aliases.

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

Use clear, imperative subject lines (for example `feat: add Mega board profile`). Group
related work into focused commits.

## License

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
