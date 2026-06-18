"""Unit tests for board protocol selection (default and per-connection override)."""

import pytest

from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from liveduino.drivers.base import Driver
from liveduino.protocols.base import ProtocolClient
from tests.shared.fake_driver import FakeDriver
from tests.shared.mock_protocol import MockProtocol


@pytest.mark.unit
def test_board_uses_default_protocol_factory() -> None:
    seen: list[Driver] = []

    class CustomBoard(Board):
        id = "test:custom"
        name = "Test Custom Board"
        digital_pins = range(1)
        analog_pins = range(1)
        pwm_pins = frozenset()

        @staticmethod
        def protocol_factory(driver: Driver) -> ProtocolClient:
            seen.append(driver)
            return MockProtocol()

    driver = FakeDriver()
    board = CustomBoard().connect(driver=driver)
    assert isinstance(board, CustomBoard)
    assert seen == [driver]


@pytest.mark.unit
def test_protocol_override_at_instantiation() -> None:
    seen: list[Driver] = []

    def protocol(driver: Driver) -> ProtocolClient:
        seen.append(driver)
        return MockProtocol()

    driver = FakeDriver()
    board = ArduinoUno(protocol=protocol).connect(driver=driver)
    assert isinstance(board, ArduinoUno)
    assert seen == [driver]
