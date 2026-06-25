"""Build the bundled StandardFirmata firmware images.

Compiles each catalog board's firmware with arduino-cli, using the board's own
``fqbn``, ``firmware_sketch`` (the primary image ``liveduino-cli flash`` writes over
serial), and ``firmware_sketches`` (extra Firmata variants such as network
transports) metadata. It writes one Intel HEX per built sketch, named after the
board model (e.g. ``standardfirmata-uno.hex``, ``standardfirmataethernet-ethernet.hex``),
plus a ``manifest.json`` into the ``liveduino.firmware`` package. The CLI uses the
primary images so ``liveduino-cli flash`` works offline, without the Arduino IDE.

Extra variants that need an uninstalled library or per-deployment configuration
(StandardFirmataEthernet needs the Ethernet library; StandardFirmataWiFi needs a
configured ``wifiConfig.h``) are skipped and recorded under ``unsupported`` rather
than failing the build.

Run it from the repo root (or via ``make firmware``):

    uv run python scripts/build_firmware.py

Requirements: arduino-cli on PATH, the ``arduino:avr`` core, and the ``Firmata``
and ``Servo`` libraries installed.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from liveduino.boards.board import Board
from liveduino.boards.registry import available_boards

_REPO_ROOT = Path(__file__).resolve().parent.parent
_FIRMWARE_DIR = _REPO_ROOT / "src" / "liveduino" / "firmware"


def _run(args: list[str]) -> str:
    """Run a subprocess and return its stdout, raising on failure."""
    result = subprocess.run(args, capture_output=True, text=True, check=True)  # noqa: S603
    return result.stdout.strip()


def _require_arduino_cli() -> str:
    """Return the arduino-cli executable path or exit with guidance."""
    executable = shutil.which("arduino-cli")
    if executable is None:
        sys.exit("arduino-cli not found on PATH; install it to build firmware")
    return executable


def _examples_dir(cli: str) -> Path:
    """Return the installed Firmata library examples directory."""
    user_dir = Path(_run([cli, "config", "get", "directories.user"]))
    return user_dir / "libraries" / "Firmata" / "examples"


def _sketch_dir(examples: Path, sketch_name: str) -> Path:
    """Locate the installed example sketch directory for a Firmata sketch."""
    sketch = examples / sketch_name
    if not (sketch / f"{sketch_name}.ino").is_file():
        sys.exit(
            f"{sketch_name} sketch not found at {sketch}; run: arduino-cli lib install Firmata"
        )
    return sketch


def _firmata_version(cli: str) -> str:
    """Return the installed Firmata library version for the manifest."""
    libraries = json.loads(_run([cli, "lib", "list", "Firmata", "--format", "json"]))
    return libraries["installed_libraries"][0]["library"]["version"]


def _compile(cli: str, sketch: Path, sketch_name: str, fqbn: str, output_dir: Path) -> bytes:
    """Compile a sketch for an FQBN and return the flash hex bytes."""
    _run([cli, "compile", "--fqbn", fqbn, "--output-dir", str(output_dir), str(sketch)])
    return (output_dir / f"{sketch_name}.ino.hex").read_bytes()


def _skip_reason(stderr: str) -> str:
    """Return a short, human-readable reason for a failed compilation."""
    if "exceeds available space" in stderr or "Not enough memory" in stderr:
        return "firmware does not fit on this board"
    return "firmware does not compile (missing library or configuration)"


def _build(
    cli: str,
    examples: Path,
    board: Board,
    sketch_name: str,
    tmp_root: Path,
    unsupported: dict[str, str],
    *,
    required: bool,
) -> bytes | None:
    """
    Compile one sketch for a board and return its hex bytes, or None if it was
    skipped. A failing primary (required) firmware aborts only when the error is
    not the expected does-not-fit case; extra (optional) firmwares never abort.
    """
    sketch = _sketch_dir(examples, sketch_name)
    model = board.fqbn.split(":")[-1]
    filename = f"{sketch_name.lower()}-{model}.hex"
    print(f"Compiling {board.name} - {sketch_name} ({board.fqbn}) -> {filename}")
    try:
        return _compile(cli, sketch, sketch_name, board.fqbn, tmp_root / filename)
    except subprocess.CalledProcessError as exc:
        reason = _skip_reason(exc.stderr or "")
        if required and reason != "firmware does not fit on this board":
            raise
        print(f"  skipped {board.name} {sketch_name}: {reason}")
        unsupported[f"{board.id} ({sketch_name})"] = reason
        return None


def main() -> int:
    """Compile primary and extra firmware for every catalog board and refresh the bundle."""
    cli = _require_arduino_cli()
    examples = _examples_dir(cli)
    firmata_version = _firmata_version(cli)

    _FIRMWARE_DIR.mkdir(parents=True, exist_ok=True)
    for stale in _FIRMWARE_DIR.glob("*.hex"):
        stale.unlink()

    boards: dict[str, dict[str, str]] = {}
    extras: dict[str, dict[str, str]] = {}
    unsupported: dict[str, str] = {}
    with tempfile.TemporaryDirectory() as tmp:
        tmp_root = Path(tmp)
        for board_id, board in sorted(available_boards().items()):
            if board.fqbn is None:
                continue
            model = board.fqbn.split(":")[-1]

            hex_bytes = _build(
                cli, examples, board, board.firmware_sketch, tmp_root, unsupported, required=True
            )
            if hex_bytes is not None:
                filename = f"{board.firmware_sketch.lower()}-{model}.hex"
                (_FIRMWARE_DIR / filename).write_bytes(hex_bytes)
                boards[board_id] = {
                    "file": filename,
                    "sha256": hashlib.sha256(hex_bytes).hexdigest(),
                    "fqbn": board.fqbn,
                    "sketch": board.firmware_sketch,
                }

            for sketch_name in board.firmware_sketches:
                hex_bytes = _build(
                    cli, examples, board, sketch_name, tmp_root, unsupported, required=False
                )
                if hex_bytes is None:
                    continue
                filename = f"{sketch_name.lower()}-{model}.hex"
                (_FIRMWARE_DIR / filename).write_bytes(hex_bytes)
                extras[filename] = {
                    "board": board_id,
                    "sketch": sketch_name,
                    "fqbn": board.fqbn,
                    "sha256": hashlib.sha256(hex_bytes).hexdigest(),
                }

    if not boards:
        sys.exit("No firmware could be built; check the arduino-cli setup")

    manifest = {
        "firmata_version": firmata_version,
        "boards": boards,
        "extras": extras,
        "unsupported": unsupported,
    }
    (_FIRMWARE_DIR / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )
    print(
        f"Wrote {len(boards)} primary image(s) and {len(extras)} extra variant(s) "
        f"to {_FIRMWARE_DIR}"
    )
    if unsupported:
        print(f"Skipped {len(unsupported)}: {', '.join(sorted(unsupported))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
