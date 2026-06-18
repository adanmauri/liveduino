"""Board auto-discovery and lookup.

Boards live in the ``liveduino.boards.catalog`` package: one file per board,
each defining a ``Board`` subclass. Dropping a new file there is enough to
register it; nothing else needs editing.
"""

from __future__ import annotations

import importlib
import pkgutil

from liveduino.boards.board import Board
from liveduino.exceptions import LiveduinoError

_CATALOG_PACKAGE = "liveduino.boards.catalog"
_BOARDS: dict[str, type[Board]] = {}
_BY_NAME: dict[str, type[Board]] = {}


def _is_board_subclass(value: object) -> bool:
    """Return True if value is a concrete Board subclass."""
    if not isinstance(value, type) or value is Board:
        return False
    return issubclass(value, Board)


def _discover() -> None:
    """Import every catalog module and register its Board subclasses."""
    package = importlib.import_module(_CATALOG_PACKAGE)
    for module_info in pkgutil.iter_modules(package.__path__):
        module = importlib.import_module(f"{_CATALOG_PACKAGE}.{module_info.name}")
        for name, value in vars(module).items():
            if _is_board_subclass(value):
                register_board(value)
                _BY_NAME[name] = value


def register_board(board: type[Board]) -> None:
    """Register a board class for connect() lookups."""
    _BOARDS[board.id] = board


def get_board(board_id: str) -> type[Board]:
    """Return a registered board class by id."""
    try:
        return _BOARDS[board_id]
    except KeyError as exc:
        raise LiveduinoError(f"Unknown board: {board_id!r}") from exc


def get_named_board(name: str) -> type[Board]:
    """Return a discovered board class by its declared name."""
    try:
        return _BY_NAME[name]
    except KeyError as exc:
        raise AttributeError(f"No board named {name!r} in liveduino.boards.catalog") from exc


def available_boards() -> dict[str, type[Board]]:
    """Return all registered board classes keyed by id."""
    return dict(_BOARDS)


_discover()
