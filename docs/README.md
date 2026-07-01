# Documentation

Reference docs for liveduino. Start with the [project README](../README.md) for the pitch,
quick start, and overview; the pages here go deeper on each topic.

## For users

| Document | Contents |
| --- | --- |
| [`API.md`](API.md) | Full Arduino method table, analog pins, servo, I2C (+ `Wire`), discovery, serial relay, and helpers |
| [`BOARDS.md`](BOARDS.md) | Supported boards and how to add one |
| [`CONNECTIONS.md`](CONNECTIONS.md) | Drivers (serial, TCP, Bluetooth) and the protocol override |
| [`CLI.md`](CLI.md) | The `liveduino-cli` command: flash firmware, list boards and ports |

## For contributors

| Document | Contents |
| --- | --- |
| [`DEVELOPMENT.md`](DEVELOPMENT.md) | Setup, `make` targets, the coverage gate, and tests |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | Layers, data flow, drivers, analog pins, and testing |

## See also

- [`../firmware/README.md`](../firmware/README.md) for flashing StandardFirmata onto the board.
- [`../AGENTS.md`](../AGENTS.md) for coding standards and guardrails.
