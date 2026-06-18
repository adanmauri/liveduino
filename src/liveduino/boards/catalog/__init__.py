"""Board catalog.

One file per board, each defining a ``Board`` subclass. Drop a new file here
and it is auto-registered; access it by name, e.g. ``catalog.ArduinoUno``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from liveduino.boards.registry import get_named_board

if TYPE_CHECKING:
    from liveduino.boards.board import Board


def __getattr__(name: str) -> type[Board]:
    """Resolve a discovered board class by name."""
    return get_named_board(name)
