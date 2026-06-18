"""Board connection helpers."""

from __future__ import annotations

from collections.abc import Callable

from liveduino.boards.board import Board
from liveduino.boards.registry import get_board
from liveduino.drivers.base import Driver
from liveduino.protocols.base import ProtocolClient


def connect(
    board_id: str,
    port: str | None = None,
    *,
    baud: int | None = None,
    driver: Driver | None = None,
    protocol: Callable[[Driver], ProtocolClient] | None = None,
) -> Board:
    """Instantiate a registered board (optionally with a protocol) and connect it."""
    return get_board(board_id)(protocol=protocol).connect(port, baud=baud, driver=driver)
