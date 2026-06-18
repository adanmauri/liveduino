"""Board base class, registry, and catalog.

Public entry point for the board layer: re-exports the ``Board`` base class and
the registry helpers used to discover and look up boards by id or name.
"""

from liveduino.boards.board import Board
from liveduino.boards.registry import (
    available_boards,
    get_board,
    get_named_board,
    register_board,
)

__all__ = [
    "Board",
    "available_boards",
    "get_board",
    "get_named_board",
    "register_board",
]
