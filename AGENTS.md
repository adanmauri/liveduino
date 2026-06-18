# AI Agents Guidelines — Liveduino

## Overview

This document defines the operational principles and coding standards for AI
agents working on **Liveduino**. Follow it to keep changes consistent, typed,
well tested, and faithful to the Arduino/Wiring API.

### Project context

**Liveduino** is a Python 3.13 library that controls microcontrollers from the
host using the **Arduino/Wiring API** (`pinMode`, `digitalWrite`, `analogRead`,
…). It is the spiritual successor to **Frameduino** (see `legacy/`).

- **MVP**: Arduino UNO with **StandardFirmata**, driven by a **native**
  `FirmataProtocol` (the Firmata 2.x wire protocol is implemented in-house over a
  `Driver`; no third-party Firmata library). Works over USB serial, TCP/WiFi,
  or Bluetooth RFCOMM by swapping the driver.
- **Goal**: zero learning curve for Arduino users — same function names and
  semantics, just in Python.
- **Not in scope**: running Python on the MCU, compiling sketches, or exposing
  Firmata wire details to users.
- **Repo**: GitHub `frameduino`; PyPI package **`liveduino`**.

For the full picture, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

### Project structure

```
src/liveduino/
├── constants.py    # Arduino constants (HIGH, LOW, INPUT, …)
├── types.py        # Arduino value types (PinMode, DigitalValue, BitOrder)
├── utilities.py    # Host value utilities (map_range, constrain)
├── boards/         # Board base class + registry
│   ├── board.py    # Board base class (Arduino API + pin map, capabilities, connect)
│   ├── registry.py # Board auto-discovery + lookup (get_board, available_boards)
│   └── catalog/    # One Board subclass per board (e.g. ArduinoUno), auto-discovered
├── protocols/      # Native FirmataProtocol; future LiveProtocol (Pinguino)
├── drivers/        # SerialDriver, TcpDriver, BluetoothDriver (SocketDriver base)
└── connection.py   # connect("arduino:uno", port)
firmware/           # MCU setup docs / future firmware
legacy/             # Frameduino 0.x (Python 2)
tests/unit/         # mocks, @pytest.mark.unit
tests/integration/  # hardware, @pytest.mark.integration, LIVEDUINO_PORT
```

**Layer rule**: User API → `Board` subclass → `ProtocolClient` →
`Driver` → firmware. Never leak protocol internals (Firmata bytes) or
driver internals through public exports.

### Board catalog

- `Board` (in `boards/board.py`) is the base class: it carries the Arduino API
  (`pinMode`, `digitalWrite`, …) plus the pin map, capabilities, and `connect`.
- Each concrete board is a **`Board` subclass** in its own file under
  `src/liveduino/boards/catalog/` (e.g. `catalog/arduino_uno.py` defines `ArduinoUno`).
- The registry **auto-discovers** every subclass: dropping a new file is enough
  to register it for `connect("<id>", port)` and `available_boards()`. Nothing
  else needs editing.
- Subclasses just set class attributes (`id`, `name`, `digital_pins`,
  `analog_pins`, `pwm_pins`, …) and may add board-specific behaviour.
- Keep `boards/catalog/` for board definitions only; the base class and registry
  live in `boards/board.py` and `boards/registry.py`.

## Core Principles

### 1. Documentation-First Approach

- **MANDATORY**: Always reference the docs before implementation.
- Start with [README.md](README.md) and [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
- Follow the established patterns documented in the architecture guide.
- **MANDATORY**: When making changes to code, configuration, or any part of the
  project that affect existing documentation (e.g. new boards, env vars,
  commands, architecture, or firmware setup), update the relevant docs
  (`README.md`, `docs/ARCHITECTURE.md`, `firmware/*/README.md`) so that
  documentation stays in sync with the implementation.

### 2. Security and Confidentiality

- **Data Protection**: Never expose sensitive data, credentials, or proprietary information
- **Secrets Management**: Use environment variables for configuration (never hardcode secrets)
- **Access Control**: Follow least privilege principles for all operations
- **Audit Trail**: Maintain clear logs of all AI-assisted changes

### 3. Code Quality Standards

- **Type Safety**: Use type hints and `Literal` types (`PinMode`, `DigitalValue`) for parameter validation
- **Error Handling**: Raise specific `liveduino.exceptions` with descriptive messages
- **Documentation**: Maintain clear docstrings and update relevant documentation

**MANDATORY**: All code must follow the detailed coding standards defined in the Code Quality Standards section below.

## Code Quality Standards

**MANDATORY**: All code must follow the detailed coding standards defined below.

### Language and Communication

- **All comments and messages must be in English**
- **Logs must not use emojis** - Use plain text messages only
- **Error messages and user-facing text must be in English**

### Python Version and Type Hints

- **Python 3.13+ syntax is required**
- Use built-in types instead of `typing` module when possible:
  - Use `dict` instead of `typing.Dict`
  - Use `list` instead of `typing.List`
  - Use `tuple` instead of `typing.Tuple`
  - Use `set` instead of `typing.Set`
- Prefer union syntax over `typing` aliases:
  - Use `type | None` instead of `Optional[type]` (e.g. `str | None`, not `Optional[str]`)
  - Use `type1 | type2` instead of `Union[type1, type2]`
- Only import from `typing` when necessary (e.g. `Any`, `Final`, `Literal`, `ClassVar`, `Protocol`, `TYPE_CHECKING`, `cast`, `overload`). Do **not** import `Optional`, `Dict`, `List`, `Tuple`, `Set`, or `Union`; use built-in types and `X | Y` syntax instead.

**Examples:**

```python
# ✅ Correct (Python 3.13+)
def process_data(data: dict[str, int]) -> list[str] | None:
    ...

def find_board(board_id: str) -> Board | None:
    ...

# ❌ Incorrect
from typing import Dict, List, Optional, Union
def process_data(data: Dict[str, int]) -> Optional[List[str]]:
    ...

def find_board(board_id: str) -> Optional[Board]:  # use Board | None instead
    ...
```

### Docstring Format

All docstrings must follow this format:

**Module-level docstrings:**

```python
"""Brief description of the module.

More detailed description that explains what the module does,
its purpose, and key concepts. Can span multiple lines to
provide comprehensive context about the module's functionality.

Additional paragraphs can be added to explain more complex
aspects or usage patterns.
"""
# Blank line after docstring
```

**Class docstrings:**

```python
class MyClass:
    """Brief description of the class.

    More detailed description explaining the class purpose,
    its main responsibilities, and how it fits into the
    larger system architecture.

    Additional context about usage patterns or important
    design decisions.
    """
    # Blank line after docstring
```

**Method/Function docstrings:**

```python
def my_method(self, param1: str, param2: int | None = None) -> dict[str, Any]:
    """Brief description of what the method does."""
    # Code immediately follows, no blank line after docstring
```

**Single-line docstrings (default):**

- Must be on a single line
- No blank line between docstring and first line of code
- Example:

```python
def supports_pwm(cls, pin: int) -> bool:
    """Return True if the digital pin supports PWM output."""
    return pin in cls.pwm_pins
```

**Multi-line docstrings (only when necessary):**

- Use only when the docstring exceeds 100 characters OR when important information needs to be displayed (e.g., lists of configuration patterns)
- Format must be:

```python
def load_board(...) -> Board:
    """
    Load a board class from the catalog. Supports multiple lookup patterns:
   - By board id (via board_id parameter)
   - By declared class name (via catalog attribute access)
   - Auto-discovered from src/liveduino/boards/catalog/
    """
    if board_id is None:
        # Code immediately follows, no blank line after docstring
```

**Multi-line docstring rules:**

- Opening `"""` must be on its own line
- Closing `"""` must be on its own line
- No blank line between docstring and first line of code
- Do NOT include "Args:", "Returns:", or "Parameters:" sections
- Use only for important information that cannot fit in a single line (e.g., lists of options, configuration patterns)

**Key docstring guidelines:**

- **Functions/Methods**: Single-line by default, multi-line only if >100 characters or requires important structured information
- **Public API methods**: Must have at least a one-line descriptive docstring. If a new public method is added without one, add at least one descriptive line (e.g. what it does or returns).
- **No blank lines**: Never add a blank line between docstring and the first line of code
- **No parameter documentation**: Do not include "Args:", "Returns:", or "Parameters:" sections
- **Multi-line format**: If multi-line, use `"""` on separate lines (not `"""text`)
- **Be descriptive and clear**: Use proper capitalization and punctuation
- **Document all public methods, classes, and modules**

### Arduino API fidelity

- Public board methods use **camelCase** to match Arduino/Wiring
  (`pinMode`, `digitalWrite`, `digitalRead`, `analogRead`, `analogWrite`,
  `tone`, `noTone`, `pulseIn`, `shiftOut`, `shiftIn`).
- Constants mirror Arduino (`INPUT`, `OUTPUT`, `INPUT_PULLUP`, `HIGH`, `LOW`,
 `LSBFIRST`, `MSBFIRST`, and analog pins `A0`-`A7`); typed via `PinMode` /
 `DigitalValue` / `BitOrder` (`Literal`) aliases.
- Host-side timing (`delay`, `delayMicroseconds`, `millis`, `micros`) are
  **`Board` methods** that run on the Python host; `millis`/`micros` count from
  the moment the board connection was created. The pure value helpers
  `map_range` and `constrain` are module-level functions.
- Operations StandardFirmata cannot perform (`tone`, `noTone`, `pulseIn`,
  `shiftOut`, `shiftIn`) keep their Arduino signatures but raise
  `UnsupportedOperationError` until a protocol supports them.

### Code Style

- Follow PEP 8 guidelines
- Use Black for formatting (line length: 100)
- Use type hints for all function/method signatures
- Use descriptive variable and function names
- Prefer explicit over implicit code
- Group imports (standard library, third-party, local) and sort with isort (Black profile)
- Use absolute imports from the `liveduino.` prefix

### Error Handling

- Use specific exception types from `liveduino.exceptions`
  (`LiveduinoError` and its subclasses) with descriptive messages in English.
- Validate user input (pins, modes, values) at the `Board` layer and fail with
  the appropriate `InvalidPinError` / `InvalidModeError` / `InvalidValueError`.
- Raise `UnsupportedOperationError` when the active protocol cannot perform an
  Arduino operation (e.g. `tone` over StandardFirmata).
- Use `NotImplementedError` for abstract methods / unimplemented protocols.

### Logging

- Use the standard `logging` module if logging is needed
- Do not use emojis in log messages
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Include context in log messages

## Dependency Management

- **Use UV for dependency management** (`pyproject.toml` + `uv.lock`).
- **Production dependencies (`[project.dependencies]`)**: declare compatible
  version constraints (e.g. `pyserial>=3.5`); exact versions are pinned by
  `uv.lock`.
- **Development dependencies (`[dependency-groups.dev]`)**: group dev-only tools
  (pytest, ruff, black, mypy, …) under `dev`.
- **Keep dependencies sorted**: entries in both lists must be in **alphabetical
  order** by package name.
- Add packages with `uv add <pkg>` (and `uv add --dev <pkg>` for dev tools);
  never hand-edit the lockfile.
- Commit `uv.lock` so builds are reproducible.
- This is a **distributable library** (`[tool.uv] package = true`).

## Testing

- **Unit tests** (`tests/unit/`, `@pytest.mark.unit`): pure logic; no hardware,
  no real serial. Use mocks (`tests/shared/`).
- **Integration tests** (`tests/integration/`, `@pytest.mark.integration`):
  require a real board via the `LIVEDUINO_PORT` environment variable.
- **Tests must only test public methods and attributes** — do not test private
  methods (those starting with `_`) or internal implementation details.
- **Tests must follow the same style guide** — same code style, docstrings, type
  hints, and formatting as the rest of the codebase.
- **`make test-coverage` requires 100% line coverage** on `src/liveduino/`
  (unit tests). Add or extend unit tests when touching uncovered code paths.

## Quality Checks (run before finishing)

Run the project's quality commands and verify they pass before completing a task:

```bash
make install-dev
make lint
make type-check
make test-coverage
LIVEDUINO_PORT=/dev/ttyACM0 make test-integration   # when hardware behaviour is in scope
make build
```

After implementation, **summarize the changes made and any residual risks**.

## Documentation

- Update [README.md](README.md), [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md),
  or `firmware/*/README.md` whenever you change the API, setup, or architecture.
- Use [TODO.md](TODO.md) for backlog only.
- Keep documentation in sync with the implementation; ask before creating new
  docs and keep examples to small snippets.

## Guardrails and Limitations

### 1. Operational Boundaries

- **No Breaking Changes**: Ensure backward compatibility for the public API; preserve Arduino/Wiring fidelity
- **No Leaky Abstractions**: Never expose protocol internals (Firmata bytes) or driver internals through public exports
- **No External Dependencies**: Avoid introducing new external dependencies without approval; prefer the standard library and the existing `pyserial` stack (Firmata and the TCP/Bluetooth drivers are implemented with the standard library)
- **Respect the Layers**: User API → `Board` subclass → `ProtocolClient` → driver/firmware; do not short-circuit layers
- **No Redundant Files**: Before creating a file, check whether the functionality already exists

### 2. Hardware Safety

- Treat the serial port and connected board as shared, stateful resources; always close connections cleanly
- Never assume a board is present in unit tests — hardware access belongs to integration tests (`LIVEDUINO_PORT`)
- Validate pins, modes, and values before sending commands to the device

## References

- [README.md](README.md)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [firmware/arduino/README.md](firmware/arduino/README.md)
- [legacy/](legacy/) — original Frameduino
