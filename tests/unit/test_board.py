"""Unit tests for the Board API.

Exercise the Arduino/Wiring methods exposed by ``Board`` (pin I/O, PWM, timing,
and device functions) along with pin and value validation, using mock drivers
and protocols.
"""

from unittest.mock import patch

import pytest

from liveduino.boards.board import Board
from liveduino.boards.catalog.arduino_ethernet import ArduinoEthernet
from liveduino.boards.catalog.arduino_nano import ArduinoNano
from liveduino.boards.catalog.arduino_uno import ArduinoUno
from liveduino.constants import A0, A5, A6, HIGH, INPUT_PULLUP, LOW, MSBFIRST, OUTPUT
from liveduino.exceptions import (
    BoardConnectionError,
    InvalidModeError,
    InvalidPinError,
    InvalidValueError,
)
from tests.shared.fake_driver import FakeDriver
from tests.shared.mock_protocol import MockProtocol


@pytest.fixture
def board() -> Board:
    protocol = MockProtocol()
    return ArduinoUno(protocol=lambda _driver: protocol).connect(driver=FakeDriver())


@pytest.mark.unit
def test_pin_mode_and_digital_write(board: Board) -> None:
    board.pinMode(13, OUTPUT)
    board.digitalWrite(13, HIGH)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.modes[13] == OUTPUT
    assert protocol.digital[13] == HIGH


@pytest.mark.unit
def test_digital_read_and_analog_read(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.digital[7] = LOW
    protocol.analog[0] = 512
    assert board.digitalRead(7) == LOW
    assert board.analogRead(0) == 512


@pytest.mark.unit
def test_analog_write_on_pwm_pin(board: Board) -> None:
    board.analogWrite(3, 128)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.pwm[3] == 128


@pytest.mark.unit
def test_servo_write_moves_servo(board: Board) -> None:
    board.servoWrite(9, 90)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.servo[9] == 90
    assert ("servo_write", (9, 90)) in protocol.calls


@pytest.mark.unit
def test_servo_write_rejects_out_of_range_angle(board: Board) -> None:
    with pytest.raises(InvalidValueError):
        board.servoWrite(9, 200)


@pytest.mark.unit
def test_servo_config_sets_pulse_range(board: Board) -> None:
    board.servoConfig(9, 600, 2400)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("servo_config", (9, 600, 2400)) in protocol.calls


@pytest.mark.unit
def test_servo_config_defaults(board: Board) -> None:
    board.servoConfig(9)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("servo_config", (9, 544, 2400)) in protocol.calls


@pytest.mark.unit
def test_servo_config_rejects_inverted_range(board: Board) -> None:
    with pytest.raises(InvalidValueError):
        board.servoConfig(9, 2400, 600)


@pytest.mark.unit
def test_reset_delegates(board: Board) -> None:
    board.reset()
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("system_reset", ()) in protocol.calls


@pytest.mark.unit
def test_sampling_interval_delegates(board: Board) -> None:
    board.samplingInterval(50)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("sampling_interval", (50,)) in protocol.calls


@pytest.mark.unit
def test_read_string_delegates(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.string = "board says hi"
    assert board.readString() == "board says hi"


@pytest.mark.unit
def test_info_returns_firmware_and_identity(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.firmware = (2, 5, "StandardFirmata")
    info = board.info()
    assert info.firmware == "StandardFirmata"
    assert info.firmwareVersion == "2.5"
    assert info.id == ArduinoUno.id
    assert info.name == ArduinoUno.name


@pytest.mark.unit
def test_pin_state_returns_named_mode_and_value(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.pin_states[13] = (0x01, 1)
    state = board.pinState(13)
    assert (state.pin, state.mode, state.value) == (13, "OUTPUT", 1)


@pytest.mark.unit
def test_capabilities_bypass_to_catalog_before_connect() -> None:
    board = ArduinoUno()  # not connected: falls back to the class definition
    caps = board.capabilities()
    assert caps.supports(3, "PWM")  # pin 3 is a PWM pin on the UNO
    assert not caps.supports(2, "PWM")  # pin 2 is not
    assert caps.supports(13, "OUTPUT")
    assert caps.analogChannels[14] == 0  # A0 maps to channel 0


@pytest.mark.unit
def test_catalog_capabilities_mark_analog_only_pins() -> None:
    caps = ArduinoNano().capabilities()  # not connected -> catalog
    # A6 (channel 6 -> pin 20) is analog-only: ANALOG but not digital.
    assert caps.supports(20, "ANALOG")
    assert not caps.supports(20, "OUTPUT")


@pytest.mark.unit
def test_capabilities_fetch_from_firmware_once_and_cache(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.capabilities = {3: [0x00, 0x01, 0x03], 4: [0x00, 0x01]}
    protocol.analog_mapping = {18: 4}
    caps = board.capabilities()
    assert caps.supports(3, "PWM")
    assert board.capabilities() is caps  # cached, not re-requested
    assert sum(1 for call in protocol.calls if call[0] == "capability_query") == 1


@pytest.mark.unit
def test_capabilities_fall_back_to_catalog_when_firmware_silent(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.fail_capabilities = True
    caps = board.capabilities()  # query fails -> catalog, no exception
    assert caps.supports(3, "PWM")  # UNO catalog


@pytest.mark.unit
def test_status_snapshots_every_pin(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    status = board.status()
    assert status.connected is True
    assert status.info.firmware == "StandardFirmata"
    assert set(status.pins) == set(board.digital_pins)


@pytest.mark.unit
def test_capabilities_override_pin_validation(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    # Pin 3 supports PWM, pin 4 only digital; analog channels are 4 and 5.
    protocol.capabilities = {3: [0x00, 0x01, 0x03], 4: [0x00, 0x01]}
    protocol.analog_mapping = {18: 4, 19: 5}
    board.capabilities()  # fetch + cache; now drives validation

    board.analogWrite(3, 100)  # pin 3 reports PWM -> allowed
    with pytest.raises(InvalidPinError):
        board.analogWrite(4, 100)  # pin 4 has no PWM per the board
    board.digitalWrite(3, HIGH)  # pin 3 is digital-capable
    with pytest.raises(InvalidPinError):
        board.digitalWrite(5, HIGH)  # pin 5 not reported at all
    assert board.analogRead(4) == 0  # channel 4 exists per the mapping
    with pytest.raises(InvalidPinError):
        board.analogRead(0)  # channel 0 not in the reported mapping


@pytest.mark.unit
def test_status_uses_cached_capabilities(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.capabilities = {3: [0x00, 0x01], 4: [0x00, 0x01]}
    protocol.analog_mapping = {}
    board.capabilities()
    status = board.status()
    assert set(status.pins) == {3, 4}


@pytest.mark.unit
def test_invalid_digital_pin_raises(board: Board) -> None:
    with pytest.raises(InvalidPinError):
        board.digitalWrite(20, HIGH)


@pytest.mark.unit
def test_invalid_analog_pin_raises(board: Board) -> None:
    with pytest.raises(InvalidPinError):
        board.analogRead(9)


@pytest.mark.unit
def test_analog_read_accepts_pin_constant(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.analog[0] = 321
    assert board.analogRead(A0) == 321
    assert ("analog_read", (0,)) in protocol.calls


@pytest.mark.unit
def test_analog_pin_constant_is_digital_capable(board: Board) -> None:
    board.pinMode(A0, OUTPUT)
    board.digitalWrite(A5, HIGH)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.modes[14] == OUTPUT
    assert protocol.digital[19] == HIGH


@pytest.mark.unit
def test_analog_only_pin_rejects_digital_use() -> None:
    protocol = MockProtocol()
    nano = ArduinoNano(protocol=lambda _driver: protocol).connect(driver=FakeDriver())
    assert nano.analogRead(A6) == 0
    assert ("analog_read", (6,)) in protocol.calls
    with pytest.raises(InvalidPinError):
        nano.pinMode(A6, OUTPUT)


@pytest.mark.unit
def test_reserved_pins_reject_io() -> None:
    protocol = MockProtocol()
    ethernet = ArduinoEthernet(protocol=lambda _driver: protocol).connect(driver=FakeDriver())
    ethernet.digitalWrite(9, HIGH)
    assert protocol.digital[9] == HIGH
    with pytest.raises(InvalidPinError):
        ethernet.pinMode(10, OUTPUT)
    with pytest.raises(InvalidPinError):
        ethernet.analogWrite(11, 128)


@pytest.mark.unit
def test_analog_constant_resolves_per_board() -> None:
    protocol = MockProtocol()

    class MegaLikeBoard(Board):
        id = "test:megalike"
        name = "Mega-like Board"
        digital_pins = range(54)
        analog_pins = range(16)
        pwm_pins = frozenset()
        first_analog_pin = 54

    board = MegaLikeBoard(protocol=lambda _driver: protocol).connect(driver=FakeDriver())
    board.digitalWrite(A0, HIGH)
    assert protocol.digital[54] == HIGH
    board.analogRead(A0)
    assert ("analog_read", (0,)) in protocol.calls


@pytest.mark.unit
def test_non_pwm_pin_analog_write_raises(board: Board) -> None:
    with pytest.raises(InvalidPinError):
        board.analogWrite(2, 10)


@pytest.mark.unit
def test_invalid_pin_mode_raises(board: Board) -> None:
    with pytest.raises(InvalidModeError):
        board.pinMode(13, 99)  # type: ignore[arg-type]


@pytest.mark.unit
def test_invalid_digital_value_raises(board: Board) -> None:
    with pytest.raises(InvalidValueError):
        board.digitalWrite(13, 2)  # type: ignore[arg-type]


@pytest.mark.unit
def test_invalid_pwm_value_raises(board: Board) -> None:
    with pytest.raises(InvalidValueError):
        board.analogWrite(3, 300)


@pytest.mark.unit
def test_input_pullup_mode(board: Board) -> None:
    board.pinMode(7, INPUT_PULLUP)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.modes[7] == INPUT_PULLUP


@pytest.mark.unit
def test_tone_and_no_tone(board: Board) -> None:
    board.tone(8, 440, 100)
    board.noTone(8)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("tone", (8, 440, 100)) in protocol.calls
    assert ("no_tone", (8,)) in protocol.calls


@pytest.mark.unit
def test_tone_default_duration(board: Board) -> None:
    board.tone(8, 440)
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert ("tone", (8, 440, None)) in protocol.calls


@pytest.mark.unit
def test_pulse_in_returns_protocol_value(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.pulse = 1234
    assert board.pulseIn(8, HIGH) == 1234
    assert ("pulse_in", (8, HIGH, 1_000_000)) in protocol.calls


@pytest.mark.unit
def test_shift_out_and_shift_in(board: Board) -> None:
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    protocol.shifted = 200
    board.shiftOut(8, 9, MSBFIRST, 170)
    assert board.shiftIn(8, 9, MSBFIRST) == 200
    assert ("shift_out", (8, 9, MSBFIRST, 170)) in protocol.calls
    assert ("shift_in", (8, 9, MSBFIRST)) in protocol.calls


@pytest.mark.unit
def test_shift_validates_clock_pin(board: Board) -> None:
    with pytest.raises(InvalidPinError):
        board.shiftOut(8, 99, MSBFIRST, 170)


@pytest.mark.unit
def test_delay_sleeps_in_seconds(board: Board) -> None:
    with patch("liveduino.boards.board.time.sleep") as mock_sleep:
        board.delay(250)
    mock_sleep.assert_called_once_with(0.25)


@pytest.mark.unit
def test_delay_microseconds_sleeps(board: Board) -> None:
    with patch("liveduino.boards.board.time.sleep") as mock_sleep:
        board.delayMicroseconds(500)
    mock_sleep.assert_called_once_with(0.0005)


@pytest.mark.unit
def test_millis_and_micros() -> None:
    with patch("liveduino.boards.board.time.monotonic", side_effect=[100.0, 101.5, 101.5]):
        timed_board = ArduinoUno()
        assert timed_board.millis() == 1500
        assert timed_board.micros() == 1_500_000


@pytest.mark.unit
def test_close_disconnects(board: Board) -> None:
    board.close()
    protocol = board._protocol
    assert isinstance(protocol, MockProtocol)
    assert protocol.connected is False


@pytest.mark.unit
def test_methods_before_connect_raise() -> None:
    board = ArduinoUno()
    with pytest.raises(BoardConnectionError):
        board.pinMode(13, OUTPUT)


@pytest.mark.unit
def test_close_before_connect_is_safe() -> None:
    ArduinoUno().close()
