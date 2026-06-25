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
| `make install-dev` | Install all deps (incl. dev) + pre-commit hooks |
| `make lint` | ruff, flake8, pylint |
| `make type-check` | mypy, pyright |
| `make security` | bandit |
| `make test-coverage` | Unit tests with 100% coverage gate |
| `make test-integration` | Integration tests (requires `LIVEDUINO_PORT`) |
| `make build` | Build the wheel |
| `make firmware` | Rebuild the bundled StandardFirmata hex (requires arduino-cli) |

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
`StandardFirmataWiFi` needs a configured `wifiConfig.h`). It requires `arduino-cli`
on PATH plus the `arduino:avr` core and the `Firmata`, `Servo`, and (for the
Ethernet variant) `Ethernet` libraries:

```bash
arduino-cli core install arduino:avr
arduino-cli lib install Firmata Servo Ethernet
make firmware
```

The `Firmware` GitHub workflow does the same in CI: it fails a pull request whose
bundled firmware is out of date, and can regenerate the images on demand
(`workflow_dispatch`) by opening a pull request.

Coding standards and guardrails for contributors (and AI agents) live in
[`AGENTS.md`](../AGENTS.md). Architecture details are in
[`docs/ARCHITECTURE.md`](ARCHITECTURE.md).
