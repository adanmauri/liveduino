"""Unit tests for boards and the registry."""

import pytest

from liveduino.boards import catalog
from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from liveduino.boards.registry import available_boards, get_board, register_board
from liveduino.exceptions import LiveduinoError


@pytest.mark.unit
def test_arduino_uno_values() -> None:
    assert ArduinoUno.id == "arduino:uno"
    assert ArduinoUno.is_valid_digital_pin(13)
    assert ArduinoUno.is_valid_analog_pin(5)
    assert ArduinoUno.supports_pwm(3)
    assert not ArduinoUno.supports_pwm(2)


@pytest.mark.unit
def test_analog_pins_double_as_digital() -> None:
    assert ArduinoUno.is_valid_digital_pin(14)
    assert ArduinoUno.is_valid_digital_pin(19)
    assert not ArduinoUno.is_valid_digital_pin(20)


@pytest.mark.unit
def test_analog_only_pins_are_not_digital_capable() -> None:
    nano = get_board("arduino:nano")
    assert nano.analog_only_pins == frozenset({6, 7})
    assert nano.is_valid_analog_pin(6)
    assert not nano.is_valid_digital_pin(20)


@pytest.mark.unit
def test_arduino_uno_is_auto_discovered() -> None:
    boards = available_boards()
    assert "arduino:uno" in boards
    assert boards["arduino:uno"] is ArduinoUno


# board_id, analog channels, supports PWM on pin 3, supports PWM on pin 10
_ATMEGA328_BOARDS = [
    ("arduino:nano", 8, True),
    ("arduino:mini", 8, True),
    ("arduino:pro", 8, True),
    ("arduino:diecimila", 6, True),
    ("arduino:ethernet", 6, True),
    ("arduino:fio", 8, True),
    ("arduino:bt", 6, True),
    ("arduino:lilypad", 6, True),
    ("arduino:atmegang", 6, True),
    ("arduino:unomini", 6, True),
]


@pytest.mark.unit
@pytest.mark.parametrize(("board_id", "analog_count", "pwm_on_10"), _ATMEGA328_BOARDS)
def test_atmega328_boards_registered(board_id: str, analog_count: int, pwm_on_10: bool) -> None:
    board = get_board(board_id)
    assert board.id == board_id
    assert board.digital_pins == range(14)
    assert len(board.analog_pins) == analog_count
    assert board.supports_pwm(3)
    assert board.supports_pwm(10) is pwm_on_10
    assert board.default_baud == 57600


@pytest.mark.unit
def test_get_board_returns_discovered_board() -> None:
    assert get_board("arduino:uno") is ArduinoUno


@pytest.mark.unit
def test_catalog_resolves_board_by_name() -> None:
    assert catalog.ArduinoUno is ArduinoUno


@pytest.mark.unit
def test_catalog_unknown_name_raises() -> None:
    with pytest.raises(AttributeError):
        _ = catalog.NotABoard


@pytest.mark.unit
def test_get_board_unknown_raises() -> None:
    with pytest.raises(LiveduinoError):
        get_board("unknown:board")


@pytest.mark.unit
def test_register_board() -> None:
    class TestBoard(Board):
        id = "test:board"
        name = "Test Board"
        digital_pins = range(2)
        analog_pins = range(1)
        pwm_pins = frozenset({1})

    register_board(TestBoard)
    assert get_board("test:board") is TestBoard


@pytest.mark.unit
def test_subclass_without_required_attrs_raises() -> None:
    with pytest.raises(TypeError):

        class IncompleteBoard(Board):
            id = "test:incomplete"


@pytest.mark.unit
def test_board_cannot_be_instantiated_directly() -> None:
    with pytest.raises(TypeError):
        Board()
