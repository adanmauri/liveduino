# Liveduino: Roadmap / deferred work

Items not implemented yet. Add entries when scope is agreed; link to issues when they exist.

## Boards

- [x] ATmega328 family: UNO, Nano, Mini, Pro/Pro Mini, Fio, Duemilanove/Diecimila, Ethernet, BT, LilyPad, UNO Mini
- [ ] Arduino Mega / Mega ADK (16 analog channels)
- [ ] Arduino Leonardo, Micro (ATmega32U4)
- [ ] Arduino Due (SAM3X8E, 32-bit ARM Cortex-M3)
- [ ] Pinguino

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
