# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Servo support over the bundled Servo library: `servoWrite`, `servoConfig`.
- I2C support: batched `i2cConfig` / `i2cWrite` / `i2cRead`, an Arduino `Wire`-style layer
  (`board.wire`), and continuous reads (`i2cReadContinuous` / `i2cValue` / `i2cStopReading`).
- Board discovery: `info()` (firmware + identity), `capabilities()` (read from the firmware
  once, cached, and used over the catalog's pin map), `pinState(pin)`, and `status()`.
- `samplingInterval(ms)` to control the board's auto-report rate.
- `readString()` to read text messages the board emits (e.g. I2C errors).
- Serial relay `board.serial(port)`, mirroring Arduino's `HardwareSerial`
  (`begin` / `write` / `available` / `read` / `end`).
- `reset()` (Firmata SYSTEM_RESET) to return the board to its power-on state.

### Fixed

- PWM and servo writes on pins above 15 now use EXTENDED_ANALOG; they previously wrapped to
  the wrong channel.

## [0.1.0]

Initial release.

### Added

- Native `FirmataProtocol` implementing StandardFirmata 2.x over a pluggable driver
  (stdlib only, no third-party Firmata library).
- Arduino-style board API (`pinMode`, `digitalWrite`, `digitalRead`, `analogRead`,
  `analogWrite`, and host-side timing) with typed pins, modes, and values.
- Auto-discovered board catalog for the ATmega328 family: UNO, Nano, Mini, Pro/Pro Mini,
  Fio, Duemilanove/Diecimila, Ethernet, BT, LilyPad, and UNO Mini.
- Drivers for USB serial, TCP (Wi-Fi/Ethernet), and Bluetooth RFCOMM.
- `liveduino-cli` console command with `flash`, `boards`, and `ports`.
- Pure-Python STK500v1 programmer and Intel HEX parser, with prebuilt StandardFirmata
  images bundled per board (flash with no Arduino toolchain).
- Firmware build pipeline (`scripts/build_firmware.py`, `make firmware`, GitHub workflow).
- 100% unit-test coverage plus skippable real-hardware integration tests.

[Unreleased]: https://github.com/adanmauri/liveduino/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/adanmauri/liveduino/releases/tag/v0.1.0
