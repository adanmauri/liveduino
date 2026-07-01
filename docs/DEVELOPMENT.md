# Development

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
uv python pin 3.13
uv sync --all-groups
make install-dev        # installs dev deps + pre-commit hooks
make check              # lint + type-check + 100% coverage gate
```

| Target | What it does |
| --- | --- |
| `make install-dev` | Install all deps (incl. dev) + pre-commit hooks + firmware toolchain |
| `make lint` | ruff, flake8, pylint |
| `make type-check` | mypy, pyright |
| `make security` | bandit |
| `make format` | black, isort, ruff --fix |
| `make check` | lint + type-check + 100% coverage gate |
| `make test-coverage` | Unit tests with 100% coverage gate |
| `make test-integration` | Integration tests (requires `LIVEDUINO_PORT`) |
| `make build` | Build the wheel |
| `make firmware-setup` | Install the pinned arduino-cli core + libraries |
| `make firmware` | Rebuild the bundled StandardFirmata hex (needs `firmware-setup`) |
| `make actions ls` / `make actions workflow-<name>` | List / trigger a GitHub Actions workflow via `gh` |

Integration tests (real hardware):

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
(`arduino:avr` core plus the `Firmata`, `Servo`, and `Ethernet` libraries — exact
versions live in the `Makefile`, shared verbatim with CI). It also installs
`arduino-cli` itself via Homebrew if missing:

```bash
make firmware-setup
make firmware
```

**Important — firmware is a CI/Linux artifact.** The bundled `.hex` are not
byte-reproducible across operating systems: the `avr-gcc` in the `arduino:avr`
core differs between macOS and Linux, so a macOS build will not match the
Linux build CI verifies against — even with identical pinned versions. So the
committed images must come from Linux. Do **not** commit locally-built firmware;
regenerate it in CI instead:

```bash
make actions workflow-firmware   # runs the Firmware workflow (workflow_dispatch)
```

The `regenerate` job compiles on Linux and pushes a `firmware/rebuild` branch (it
opens a PR too if the repo allows Actions to create PRs). The `verify` job fails a
push/PR whose bundled firmware is out of date.

Coding standards and guardrails for contributors (and AI agents) live in
[`AGENTS.md`](../AGENTS.md). Architecture details are in
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
