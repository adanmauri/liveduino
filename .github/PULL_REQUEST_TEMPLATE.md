## Summary

-

## Test plan

- [ ] `make test-coverage` (required when `src/liveduino/` changed — 100% unit coverage gate)
- [ ] `LIVEDUINO_PORT=/dev/ttyACM0 make test-integration` (when hardware behaviour changed — requires a connected board)
- [ ] `make quality` (lint + type-check + security, if code changed)
- [ ] Docs updated (`README.md` / `docs/ARCHITECTURE.md` / `firmware/*/README.md`, if behavior/API/setup changed)

## Notes

<!-- risks, follow-ups, breaking changes, Arduino/Wiring API fidelity -->
