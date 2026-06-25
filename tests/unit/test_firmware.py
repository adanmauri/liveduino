"""Unit tests for the bundled firmware resolver.

Cover loading a board's bundled firmware (primary and extra variants), listing a
board's available firmwares, the default package location, and the error paths
(missing manifest, unknown board, unknown firmware, integrity failure), all
against a temporary firmware directory.
"""

import hashlib
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from liveduino.exceptions import FlashError
from liveduino.programmers.firmware import available_firmwares, load_bundled_firmware

_HEX = ":00000001FF\n"
_EXTRA_HEX = ":00000001AA\n"


def _sha(text: str) -> str:
    """Return the SHA-256 hex digest of an ASCII string."""
    return hashlib.sha256(text.encode("ascii")).hexdigest()


def _write_bundle(base: Path, board_id: str, hex_text: str, *, sha256: str | None = None) -> None:
    """Write a manifest and hex file describing one board into a directory."""
    data = hex_text.encode("ascii")
    (base / "fw.hex").write_bytes(data)
    digest = hashlib.sha256(data).hexdigest() if sha256 is None else sha256
    manifest = {"boards": {board_id: {"file": "fw.hex", "sha256": digest}}}
    (base / "manifest.json").write_text(json.dumps(manifest), encoding="ascii")


def _write_full_bundle(base: Path) -> None:
    """Write a manifest with a primary image, an extra variant, and another board."""
    (base / "primary.hex").write_bytes(_HEX.encode("ascii"))
    (base / "extra.hex").write_bytes(_EXTRA_HEX.encode("ascii"))
    manifest = {
        "boards": {
            "arduino:ethernet": {
                "file": "primary.hex",
                "sha256": _sha(_HEX),
                "sketch": "StandardFirmata",
            }
        },
        "extras": {
            "extra.hex": {
                "board": "arduino:ethernet",
                "sketch": "StandardFirmataEthernet",
                "sha256": _sha(_EXTRA_HEX),
            },
            "other.hex": {
                "board": "arduino:other",
                "sketch": "StandardFirmata",
                "sha256": _sha(_HEX),
            },
        },
    }
    (base / "manifest.json").write_text(json.dumps(manifest), encoding="ascii")


@pytest.mark.unit
def test_load_bundled_firmware(tmp_path: Path) -> None:
    _write_bundle(tmp_path, "arduino:uno", _HEX)
    assert load_bundled_firmware("arduino:uno", firmware_dir=tmp_path) == _HEX


@pytest.mark.unit
@patch("liveduino.programmers.firmware.files")
def test_load_bundled_firmware_uses_package_dir(mock_files: object, tmp_path: Path) -> None:
    mock_files.return_value = tmp_path  # type: ignore[attr-defined]
    _write_bundle(tmp_path, "arduino:uno", _HEX)
    assert load_bundled_firmware("arduino:uno") == _HEX


@pytest.mark.unit
def test_missing_manifest_raises(tmp_path: Path) -> None:
    with pytest.raises(FlashError, match="No bundled firmware found"):
        load_bundled_firmware("arduino:uno", firmware_dir=tmp_path)


@pytest.mark.unit
def test_unknown_board_raises(tmp_path: Path) -> None:
    _write_bundle(tmp_path, "arduino:uno", _HEX)
    with pytest.raises(FlashError, match="No bundled firmware for board"):
        load_bundled_firmware("arduino:nope", firmware_dir=tmp_path)


@pytest.mark.unit
def test_integrity_check_failure_raises(tmp_path: Path) -> None:
    _write_bundle(tmp_path, "arduino:uno", _HEX, sha256="0" * 64)
    with pytest.raises(FlashError, match="integrity check"):
        load_bundled_firmware("arduino:uno", firmware_dir=tmp_path)


@pytest.mark.unit
def test_available_firmwares_lists_primary_and_extras(tmp_path: Path) -> None:
    _write_full_bundle(tmp_path)
    assert available_firmwares("arduino:ethernet", firmware_dir=tmp_path) == [
        "StandardFirmata",
        "StandardFirmataEthernet",
    ]


@pytest.mark.unit
def test_available_firmwares_unknown_board_is_empty(tmp_path: Path) -> None:
    _write_full_bundle(tmp_path)
    assert available_firmwares("arduino:nope", firmware_dir=tmp_path) == []


@pytest.mark.unit
def test_load_primary_by_sketch_name(tmp_path: Path) -> None:
    _write_full_bundle(tmp_path)
    text = load_bundled_firmware("arduino:ethernet", "StandardFirmata", firmware_dir=tmp_path)
    assert text == _HEX


@pytest.mark.unit
def test_load_extra_variant_by_sketch_name(tmp_path: Path) -> None:
    _write_full_bundle(tmp_path)
    text = load_bundled_firmware(
        "arduino:ethernet", "StandardFirmataEthernet", firmware_dir=tmp_path
    )
    assert text == _EXTRA_HEX


@pytest.mark.unit
def test_unknown_firmware_lists_available(tmp_path: Path) -> None:
    _write_full_bundle(tmp_path)
    with pytest.raises(FlashError, match="available: StandardFirmata, StandardFirmataEthernet"):
        load_bundled_firmware("arduino:ethernet", "StandardFirmataWiFi", firmware_dir=tmp_path)
