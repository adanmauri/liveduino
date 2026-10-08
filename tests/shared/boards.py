"""Connected-board helpers shared by the unit tests.

Build an ``ArduinoUno`` wired to a ``MockProtocol`` over a ``FakeDriver``, and
recover that mock from a board, so each test module does not repeat the setup.
"""

from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from tests.shared.fake_driver import FakeDriver
from tests.shared.mock_protocol import MockProtocol


def connected_uno() -> Board:
    """Return an ArduinoUno connected to a fresh MockProtocol over a FakeDriver."""
    protocol = MockProtocol()
    return ArduinoUno(protocol=lambda _driver: protocol).connect(driver=FakeDriver())


def mock_protocol_of(board: Board) -> MockProtocol:
    """Return the MockProtocol that a board built by connected_uno talks to."""
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    return protocol
