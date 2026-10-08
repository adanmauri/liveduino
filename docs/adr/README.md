# Architecture Decision Records

One file per decision: `NNNN-<kebab-slug>.md` whose first line is `# NNNN. <Title>`, numbered
sequentially and never renumbered. A superseded ADR stays in place with its status changed and a
link to its successor. Start from [`template.md`](template.md).

The ADR holds the rationale; the rules in [`.agents/rules/`](../../.agents/rules/) hold the
checklist and cite the ADR instead of repeating it. `make check` fails on a numbering gap, a
heading that disagrees with its file name, an ADR missing from this index, or a broken relative
link anywhere in the docs. A number taken by a branch that has not merged yet goes under
**Reserved** so it is not reported as a gap.

| ADR                                                                               | Title                                                              | Status   |
|-----------------------------------------------------------------------------------|--------------------------------------------------------------------|----------|
| [0001](0001-uv-is-the-development-toolchain.md)                                   | uv is the development toolchain                                    | Accepted |
| [0002](0002-quality-gates-pre-commit-locally-megalinter-in-ci.md)                 | Quality gates: pre-commit locally, MegaLinter in CI                | Accepted |
| [0003](0003-non-python-linter-versions-follow-the-megalinter-image.md)            | Non-Python linter versions follow the MegaLinter image             | Accepted |
| [0004](0004-agent-assets-live-in-agents-with-generated-pointers.md)               | Agent assets live in `.agents/` with generated pointers            | Accepted |
| [0005](0005-pull-requests-check-what-they-change-main-checks-everything.md)       | Pull requests check what they change; main checks everything       | Accepted |
| [0006](0006-actions-are-pinned-to-a-commit.md)                                    | Actions are pinned to a commit                                     | Accepted |
| [0007](0007-the-public-api-mirrors-arduino-wiring.md)                             | The public API mirrors Arduino/Wiring                              | Accepted |
| [0008](0008-board-protocol-and-driver-are-separate-layers.md)                     | Board, protocol and driver are separate layers                     | Accepted |
| [0009](0009-firmata-is-implemented-in-house-over-standardfirmata.md)              | Firmata is implemented in-house, over StandardFirmata              | Accepted |
| [0010](0010-timing-runs-on-the-host.md)                                           | Timing runs on the host                                            | Accepted |
| [0011](0011-unsupported-operations-keep-their-arduino-signature-and-raise.md)     | Unsupported operations keep their Arduino signature and raise      | Accepted |
| [0012](0012-boards-are-auto-discovered-and-the-firmware-overrides-the-catalog.md) | Boards are auto-discovered, and the firmware overrides the catalog | Accepted |
| [0013](0013-the-runtime-depends-only-on-the-standard-library-and-pyserial.md)     | The runtime depends only on the standard library and pyserial      | Accepted |
| [0014](0014-firmware-is-bundled-and-flashed-in-pure-python.md)                    | Firmware is bundled and flashed in pure Python                     | Accepted |
| [0015](0015-python-3-13-is-the-minimum-version.md)                                | Python 3.13 is the minimum version                                 | Accepted |
| [0016](0016-pinguino-boards-speak-firmata.md)                                     | Pinguino boards speak Firmata                                      | Proposed |

## Reserved

None.
