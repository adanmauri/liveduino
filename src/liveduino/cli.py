"""Command-line interface for liveduino.

Exposes the ``liveduino-cli`` console command with subcommands to flash firmware
to a board over its bootloader (no external toolchain), list the boards in the
catalog (and a board's available firmwares), and list the serial ports available
on the host.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import sys
from pathlib import Path

import serial.tools.list_ports

from liveduino.boards.registry import available_boards, get_board
from liveduino.exceptions import FlashError, LiveduinoError
from liveduino.programmers.firmware import available_firmwares, load_bundled_firmware
from liveduino.programmers.intel_hex import parse_intel_hex
from liveduino.programmers.stk500v1 import Stk500v1Programmer


def _version() -> str:
    """Return the installed liveduino version, or 'unknown' if undetermined."""
    try:
        return importlib.metadata.version("liveduino")
    except importlib.metadata.PackageNotFoundError:  # pragma: no cover
        return "unknown"


def _cmd_flash(args: argparse.Namespace) -> int:
    """Flash a firmware image to a board over its serial bootloader."""
    board = get_board(args.board)
    if args.hex is None:
        text = load_bundled_firmware(args.board, args.firmware)
        source = f"bundled {args.firmware or board.firmware_sketch}"
    else:
        try:
            text = Path(args.hex).read_text(encoding="ascii")
        except OSError as exc:
            raise FlashError(f"Cannot read firmware file {args.hex!r}: {exc}") from exc
        source = args.hex
    firmware = parse_intel_hex(text)
    baud = board.flash_baud if args.baud is None else args.baud
    programmer = Stk500v1Programmer(args.port, baud=baud, page_size=board.flash_page_size)
    print(f"Flashing {len(firmware)} bytes ({source}) to {board.name} on {args.port}...")
    programmer.flash(firmware, verify=not args.no_verify)
    print("Done.")
    return 0


def _print_table(rows: list[tuple[str, str]]) -> None:
    """Print two-column rows with the first column padded to align the second."""
    width = max(len(left) for left, _ in rows)
    for left, right in rows:
        print(f"{left.ljust(width)}  {right}".rstrip())


def _cmd_boards(args: argparse.Namespace) -> int:
    """List boards in the catalog, or the firmwares available for one board."""
    if args.board is None:
        boards = sorted(available_boards().items())
        if args.vendor is not None:
            boards = [(bid, b) for bid, b in boards if bid.split(":", 1)[0] == args.vendor]
        _print_table([(board_id, board.name) for board_id, board in boards])
        return 0
    board = get_board(args.board)
    firmwares = available_firmwares(args.board)
    if not firmwares:
        print(f"No bundled firmware for {args.board}.")
        return 0
    _print_table(
        [(name, "(default)" if name == board.firmware_sketch else "") for name in firmwares]
    )
    return 0


def _cmd_ports(_args: argparse.Namespace) -> int:
    """Print the serial ports detected on the host."""
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("No serial ports found.")
        return 0
    _print_table([(info.device, info.description) for info in ports])
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with the flash, boards, and ports subcommands."""
    parser = argparse.ArgumentParser(
        prog="liveduino-cli",
        description="Live Wiring commands from Python to your microcontroller.",
    )
    parser.add_argument("--version", action="version", version=f"liveduino-cli {_version()}")
    subparsers = parser.add_subparsers(dest="command")

    flash_parser = subparsers.add_parser(
        "flash", help="Flash firmware to a board over its bootloader"
    )
    flash_parser.add_argument("board", help="Board id, e.g. arduino:uno")
    flash_parser.add_argument(
        "firmware",
        nargs="?",
        default=None,
        help="Firmware name to flash (default: the board's primary firmware)",
    )
    flash_parser.add_argument(
        "--port", required=True, help="Serial port, e.g. /dev/ttyACM0 or COM3"
    )
    flash_parser.add_argument(
        "--hex",
        metavar="PATH",
        help="Flash this Intel HEX file instead of a bundled image",
    )
    flash_parser.add_argument(
        "--baud", type=int, default=None, help="Override the bootloader baud rate"
    )
    flash_parser.add_argument(
        "--no-verify", action="store_true", help="Skip read-back verification"
    )
    flash_parser.set_defaults(handler=_cmd_flash)

    boards_parser = subparsers.add_parser(
        "boards", help="List the boards in the catalog, or a board's firmwares"
    )
    boards_parser.add_argument(
        "board", nargs="?", default=None, help="Board id; list the firmwares available for it"
    )
    boards_parser.add_argument(
        "sub", nargs="?", choices=["firmwares"], help=argparse.SUPPRESS
    )
    boards_parser.add_argument(
        "--vendor",
        choices=sorted({bid.split(":", 1)[0] for bid in available_boards()}),
        default=None,
        help="List only boards from this vendor (e.g. arduino, pinguino)",
    )
    boards_parser.set_defaults(handler=_cmd_boards)

    ports_parser = subparsers.add_parser("ports", help="List serial ports on the host")
    ports_parser.set_defaults(handler=_cmd_ports)

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the liveduino console command."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    try:
        return int(args.handler(args))
    except LiveduinoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
