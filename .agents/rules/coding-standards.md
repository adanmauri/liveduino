---
description: Coding standards for AI agents and humans working in Liveduino
---

# Rules: coding standards

Binding checklist. The tools enforce most of it: `make check` locally, MegaLinter in CI
([ADR-0002](../../docs/adr/0002-quality-gates-pre-commit-locally-megalinter-in-ci.md)). The map
of which tool runs where is in [`docs/CI.md`](../../docs/CI.md).

## Language

- All code, comments, docs, commit messages, log lines and user-facing text in **English**.
- No emojis in logs or messages.
- Never use the em dash character (U+2014): use a comma, colon, parentheses or a period instead.
  This applies to docs, comments, commit messages and any other text.

## Python: [ADR-0015](../../docs/adr/0015-python-3-13-is-the-minimum-version.md)

- **Python 3.13+** syntax.
- Built-in generics and unions: `dict[str, int]`, `list[str] | None`, `Board | None`. Import from
  `typing` only what has no built-in form (`Any`, `Final`, `Literal`, `ClassVar`, `Protocol`,
  `TYPE_CHECKING`, `cast`, `overload`). NEVER import `Optional`, `Dict`, `List`, `Tuple`, `Set` or
  `Union`.
- Use `Literal` aliases (`PinMode`, `DigitalValue`, `BitOrder`) for parameters with a fixed set of
  values.
- Type hints on every function and method signature.
- PEP 8; Black and isort (Black profile), line length 100; Ruff, Flake8, Pylint, mypy and Pyright
  clean.
- Absolute imports with the `liveduino.` prefix, grouped standard library, third-party, local.
- Descriptive names; explicit over implicit.
- Standard `logging` when logging is needed, at the right level, with context in the message.

## Docstrings

Every module, class and public function or method has one. A public API method gets at least one
descriptive line.

- **Module and class:** a one-line summary, a blank line, then the detail (purpose, key concepts,
  how it fits the architecture). A blank line follows the closing `"""`.
- **Function and method, single line (the default):** one line, and the code starts on the next
  line with no blank line in between.

  ```python
  def supports_pwm(cls, pin: int) -> bool:
      """Return True if the digital pin supports PWM output."""
      return pin in cls.pwm_pins
  ```

- **Function and method, multi-line:** only when the text exceeds 100 characters or carries
  structured information (a list of options or patterns). The opening and closing `"""` sit on
  their own lines, and the code starts right after, with no blank line.

  ```python
  def load_board(...) -> Board:
      """
      Load a board class from the catalog. Supports multiple lookup patterns:
      - By board id (via board_id parameter)
      - Auto-discovered from src/liveduino/boards/catalog/
      """
      if board_id is None:
  ```

- NEVER write `Args:`, `Returns:` or `Parameters:` sections.
- Proper capitalization and punctuation.

## Tests

- **Unit** (`tests/unit/`, `@pytest.mark.unit`): pure logic, no hardware and no real serial port;
  mocks live in `tests/shared/`.
- **Integration** (`tests/integration/`, `@pytest.mark.integration`): need a real board through
  `LIVEDUINO_PORT`, and skip without one.
- Test public methods and attributes only, never `_private` ones or implementation details.
- Tests follow this same style guide: docstrings, type hints, formatting.
- `make test-coverage` requires **100% line coverage** of `src/liveduino/`. Touching an uncovered
  path means adding or extending unit tests.

## Dependencies: [ADR-0001](../../docs/adr/0001-uv-is-the-development-toolchain.md)

- **uv** for everything: `uv sync`, `uv run`, `uv add`. NEVER call `pip` or create a virtualenv by
  hand, and never hand-edit `uv.lock`, which is committed.
- Runtime dependencies (`[project.dependencies]`) declare compatible ranges (`pyserial>=3.5`);
  `uv.lock` pins them. Adding one needs approval: prefer the standard library and the existing
  `pyserial` stack
  ([ADR-0013](../../docs/adr/0013-the-runtime-depends-only-on-the-standard-library-and-pyserial.md)).
- Development tools live in the `test` and `lint` dependency groups (`dev` includes both). Add one
  with `uv add --group <test|lint> <package>`.
- Keep every dependency list in **alphabetical order**.
- The non-Python hooks in `.pre-commit-config.yaml` pin the MegaLinter image's version and move
  only with it ([ADR-0003](../../docs/adr/0003-non-python-linter-versions-follow-the-megalinter-image.md)).
  NEVER bump one on its own.

## Workflows: [ADR-0006](../../docs/adr/0006-actions-are-pinned-to-a-commit.md)

- Every `uses:` is pinned to a full commit SHA with the version in a comment
  (`@<sha> # v7.0.1`), and a `docker://` image to its digest (`:vX.Y.Z@sha256:...`).
  `persist-credentials: false` on every checkout whose job does not push.
- Every workflow starts with `permissions: {}`; each job asks for what it needs.
- A tag, release or package that disappeared or moved is a signal, not housekeeping: read the
  upstream advisories and check this repository's runs before replacing it.
- What a tool's container ships (versions, venvs, uv) is read from its Dockerfile at the pinned
  commit, never assumed.

## Docs

- A change to the API, boards, env vars, commands, setup, firmware or architecture updates the
  docs it affects in the same change: `README.md`, `docs/*.md`, `firmware/*/README.md`.
- `TODO.md` is the backlog, nothing else.
- Ask before creating a new doc; keep examples to small snippets.
- A change that reverses or extends a recorded decision comes with a new ADR in
  [`docs/adr/`](../../docs/adr/README.md).
