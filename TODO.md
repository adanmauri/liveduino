# Liveduino: Roadmap / deferred work

Items not implemented yet. Add entries when scope is agreed; link to issues when they exist.

## Protocol / API (StandardFirmata)

- [x] Digital/analog I/O, PWM, and host-side timing
- [x] Servo (`servoWrite`, `servoConfig`)
- [x] I2C: `i2cConfig`/`i2cWrite`/`i2cRead`, Arduino `Wire` layer, continuous reads
- [x] Extended analog (PWM/servo on pins above 15)
- [x] Discovery: `info`, `capabilities` (cached, overrides the catalog), `pinState`, `status`
- [x] `samplingInterval`, `readString` (board messages), serial relay (`board.serial`)
- [x] `reset` (SYSTEM_RESET)
- [ ] `tone` / `noTone` / `pulseIn` / `shiftOut` / `shiftIn` — not defined by the Firmata
      protocol (absent from StandardFirmata and StandardFirmataPlus). Needs custom firmware:
      a StandardFirmata/ConfigurableFirmata build with a bespoke sysex per function plus the
      matching sysex on the client. See `docs/ARCHITECTURE.md`.

## Boards

- [x] ATmega328 family: UNO, Nano, Mini, Pro/Pro Mini, Fio, Duemilanove/Diecimila, Ethernet, BT, LilyPad, UNO Mini
- [ ] Arduino Mega / Mega ADK (16 analog channels)
- [ ] Arduino Leonardo, Micro (ATmega32U4)
- [ ] Arduino Due (SAM3X8E, 32-bit ARM Cortex-M3)
- [~] Pinguino 8-bit (PIC18F): 13 boards (14K50/2455/2550/2553/25K50/26J50/27J53/4455/4550/
      4553/45K50/46J50/47J53) + `PinguinoFirmata` firmware done; firmware untested on
      hardware, pin maps provisional (refined by capability query)
- [ ] Pinguino 32 (PIC32MX, 32-bit): not started

## Drivers

- [x] Serial
- [x] TCP (WiFi/Ethernet)
- [x] Bluetooth RFCOMM (Linux AF_BLUETOOTH)
- [ ] Bluetooth BLE (bleak)

## Programmers / CLI

- [x] STK500v1 programmer (ATmega328 family, pure Python)
- [x] `liveduino-cli` CLI: `flash`, `boards`, `ports`
- [x] Bundle prebuilt StandardFirmata `.hex` per board (flash with no `--hex`)
- [x] Firmware build pipeline (scripts/build_firmware.py, make firmware, GitHub workflow)
- [x] Flashing integration test on real hardware (LIVEDUINO_FLASH_PORT)
- [ ] Caterina/AVR109 programmer (Leonardo, Micro)
- [ ] SAM-BA/BOSSA programmer (MKR, Nano 33 IoT)
