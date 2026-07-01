# Pinguino firmware (planned)

Pinguino support is planned. The original idea was a modernized text command interpreter
evolved from the original [Frameduino](https://github.com/adanmauri/frameduino)
`pinguino/usb_interpreter.pde` (a `LiveProtocol`).

**Work in progress lives in the
[`experimental`](https://github.com/adanmauri/liveduino/tree/experimental) branch**, which
explores a Firmata-based approach instead: a `PinguinoFirmata` firmware for 8-bit PIC18F
boards that speaks the same wire protocol as StandardFirmata, so liveduino's existing
`FirmataProtocol` drives a Pinguino with no new protocol client. Not merged to `main` yet.

See [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md#future-pinguino).
