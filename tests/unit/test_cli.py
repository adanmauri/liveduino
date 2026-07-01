"""Unit tests for the liveduino command-line interface.

Cover the flash, boards (with firmware listing), and ports subcommands, version
output, the no-command help path, and the error handling for unknown boards and
unreadable files.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from liveduino.cli import main

_EOF_HEX = ":00000001FF\n"


@pytest.mark.unit
def test_no_command_prints_help(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 1
    assert "usage" in capsys.readouterr().out.lower()


@pytest.mark.unit
def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        main(["--version"])
    assert "liveduino" in capsys.readouterr().out


@pytest.mark.unit
def test_boards_lists_catalog(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["boards"]) == 0
    output = capsys.readouterr().out
    assert "arduino:uno" in output
    assert "Arduino UNO" in output
    assert "pinguino:4550" in output  # all vendors by default


@pytest.mark.unit
def test_boards_filters_by_vendor(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["boards", "--vendor", "pinguino"]) == 0
    output = capsys.readouterr().out
    assert "pinguino:4550" in output
    assert "arduino:uno" not in output


@pytest.mark.unit
def test_boards_lists_firmwares(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["boards", "arduino:ethernet", "firmwares"]) == 0
    output = capsys.readouterr().out
    assert "StandardFirmata" in output
    assert "StandardFirmataEthernet" in output
    assert "(default)" in output


@pytest.mark.unit
def test_boards_firmwares_unknown_board(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["boards", "nope", "firmwares"]) == 1
    assert "error:" in capsys.readouterr().err


@pytest.mark.unit
@patch("liveduino.cli.available_firmwares", return_value=[])
def test_boards_firmwares_none_bundled(
    _mock_available: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["boards", "arduino:uno"]) == 0
    assert "No bundled firmware" in capsys.readouterr().out


@pytest.mark.unit
@patch("liveduino.cli.serial.tools.list_ports.comports")
def test_ports_lists_devices(mock_comports: MagicMock, capsys: pytest.CaptureFixture[str]) -> None:
    info = MagicMock()
    info.device = "/dev/ttyACM0"
    info.description = "Arduino UNO"
    mock_comports.return_value = [info]
    assert main(["ports"]) == 0
    output = capsys.readouterr().out
    assert "/dev/ttyACM0" in output
    assert "Arduino UNO" in output


@pytest.mark.unit
@patch("liveduino.cli.serial.tools.list_ports.comports", return_value=[])
def test_ports_when_none_found(
    _mock_comports: MagicMock, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["ports"]) == 0
    assert "No serial ports found." in capsys.readouterr().out


@pytest.mark.unit
@patch("liveduino.cli.Stk500v1Programmer")
def test_flash_success(
    mock_programmer_cls: MagicMock, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    hex_file = tmp_path / "firmware.hex"
    hex_file.write_text(_EOF_HEX, encoding="ascii")
    programmer = MagicMock()
    mock_programmer_cls.return_value = programmer
    assert main(["flash", "arduino:uno", "--port", "/dev/ttyACM0", "--hex", str(hex_file)]) == 0
    mock_programmer_cls.assert_called_once_with("/dev/ttyACM0", baud=115200, page_size=128)
    programmer.flash.assert_called_once_with(b"", verify=True)
    assert "Done." in capsys.readouterr().out


@pytest.mark.unit
@patch("liveduino.cli.load_bundled_firmware", return_value=_EOF_HEX)
@patch("liveduino.cli.Stk500v1Programmer")
def test_flash_uses_bundled_firmware_by_default(
    mock_programmer_cls: MagicMock,
    mock_bundled: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    programmer = MagicMock()
    mock_programmer_cls.return_value = programmer
    assert main(["flash", "arduino:uno", "--port", "/dev/ttyACM0"]) == 0
    mock_bundled.assert_called_once_with("arduino:uno", None)
    programmer.flash.assert_called_once_with(b"", verify=True)
    assert "bundled StandardFirmata" in capsys.readouterr().out


@pytest.mark.unit
@patch("liveduino.cli.load_bundled_firmware", return_value=_EOF_HEX)
@patch("liveduino.cli.Stk500v1Programmer")
def test_flash_with_selected_firmware(
    mock_programmer_cls: MagicMock,
    mock_bundled: MagicMock,
    capsys: pytest.CaptureFixture[str],
) -> None:
    programmer = MagicMock()
    mock_programmer_cls.return_value = programmer
    exit_code = main(
        ["flash", "arduino:ethernet", "StandardFirmataEthernet", "--port", "/dev/ttyACM0"]
    )
    assert exit_code == 0
    mock_bundled.assert_called_once_with("arduino:ethernet", "StandardFirmataEthernet")
    assert "bundled StandardFirmataEthernet" in capsys.readouterr().out


@pytest.mark.unit
@patch("liveduino.cli.Stk500v1Programmer")
def test_flash_with_baud_override_and_no_verify(
    mock_programmer_cls: MagicMock, tmp_path: Path
) -> None:
    hex_file = tmp_path / "firmware.hex"
    hex_file.write_text(_EOF_HEX, encoding="ascii")
    programmer = MagicMock()
    mock_programmer_cls.return_value = programmer
    exit_code = main(
        [
            "flash",
            "arduino:uno",
            "--port",
            "/dev/ttyACM0",
            "--hex",
            str(hex_file),
            "--baud",
            "57600",
            "--no-verify",
        ]
    )
    assert exit_code == 0
    mock_programmer_cls.assert_called_once_with("/dev/ttyACM0", baud=57600, page_size=128)
    programmer.flash.assert_called_once_with(b"", verify=False)


@pytest.mark.unit
def test_flash_unknown_board(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    hex_file = tmp_path / "firmware.hex"
    hex_file.write_text(_EOF_HEX, encoding="ascii")
    exit_code = main(["flash", "nope", "--port", "/dev/ttyACM0", "--hex", str(hex_file)])
    assert exit_code == 1
    assert "error:" in capsys.readouterr().err


@pytest.mark.unit
def test_flash_missing_file(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    missing = tmp_path / "absent.hex"
    exit_code = main(["flash", "arduino:uno", "--port", "/dev/ttyACM0", "--hex", str(missing)])
    assert exit_code == 1
    assert "Cannot read firmware file" in capsys.readouterr().err
