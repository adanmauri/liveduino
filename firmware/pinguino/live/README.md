# Pinguino LiveProtocol firmware (superseded)

The original [Frameduino](https://github.com/adanmauri/frameduino) plan was a custom text
command interpreter evolved from `pinguino/usb_interpreter.pde` (a `LiveProtocol`).

**Superseded by Firmata.** Pinguino now runs [`../firmata/`](../firmata/) —
`PinguinoFirmata`, which speaks the same Firmata wire protocol as StandardFirmata, so
liveduino drives it with the existing `FirmataProtocol` instead of a new protocol client.

See [`docs/ARCHITECTURE.md`](../../../docs/ARCHITECTURE.md).
