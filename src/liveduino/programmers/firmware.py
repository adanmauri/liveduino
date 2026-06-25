"""Resolve bundled firmware images.

Looks up the prebuilt firmware shipped in the ``liveduino.firmware`` package for
a given board id (and optional firmware variant), verifies its integrity against
the manifest, and returns the Intel HEX text ready to flash. This is what
``liveduino-cli flash`` uses when no ``--hex`` file is given, so flashing works
offline.
"""

from __future__ import annotations

import hashlib
import json
from importlib.resources import files
from pathlib import Path
from typing import Any

from liveduino.exceptions import FlashError

_MANIFEST_NAME = "manifest.json"


def _bundled_dir() -> Path:
    """Return the directory of the bundled firmware package."""
    return Path(str(files("liveduino.firmware")))


def _read_manifest(base: Path) -> dict[str, Any]:
    """Load and parse the bundled firmware manifest, or raise FlashError."""
    try:
        return json.loads((base / _MANIFEST_NAME).read_text(encoding="ascii"))
    except OSError as exc:
        raise FlashError(
            "No bundled firmware found; run 'make firmware' or pass --hex with a file"
        ) from exc


def _firmware_names(manifest: dict[str, Any], board_id: str) -> list[str]:
    """Return the firmware sketch names bundled for a board (primary first)."""
    names: list[str] = []
    primary = manifest.get("boards", {}).get(board_id)
    if primary is not None:
        names.append(primary["sketch"])
    for entry in manifest.get("extras", {}).values():
        if entry.get("board") == board_id:
            names.append(entry["sketch"])
    return names


def _select_entry(
    manifest: dict[str, Any], board_id: str, sketch: str | None
) -> dict[str, Any]:
    """Return the manifest entry for a board's firmware, or raise FlashError."""
    primary = manifest.get("boards", {}).get(board_id)
    if sketch is None:
        if primary is None:
            raise FlashError(
                f"No bundled firmware for board {board_id!r}; pass --hex with a firmware file"
            )
        return primary
    if primary is not None and primary.get("sketch") == sketch:
        return primary
    for filename, entry in manifest.get("extras", {}).items():
        if entry.get("board") == board_id and entry.get("sketch") == sketch:
            return {"file": filename, "sha256": entry["sha256"]}
    available = ", ".join(_firmware_names(manifest, board_id)) or "none"
    raise FlashError(
        f"No bundled {sketch!r} firmware for board {board_id!r}; available: {available}"
    )


def available_firmwares(board_id: str, *, firmware_dir: Path | None = None) -> list[str]:
    """Return the bundled firmware sketch names available for a board id."""
    base = _bundled_dir() if firmware_dir is None else firmware_dir
    return _firmware_names(_read_manifest(base), board_id)


def load_bundled_firmware(
    board_id: str, sketch: str | None = None, *, firmware_dir: Path | None = None
) -> str:
    """Return the bundled Intel HEX text for a board id and optional firmware variant."""
    base = _bundled_dir() if firmware_dir is None else firmware_dir
    entry = _select_entry(_read_manifest(base), board_id, sketch)
    data = (base / entry["file"]).read_bytes()
    if hashlib.sha256(data).hexdigest() != entry["sha256"]:
        raise FlashError(f"Bundled firmware for {board_id!r} failed its integrity check")
    return data.decode("ascii")
