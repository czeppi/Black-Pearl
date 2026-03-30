from both_base import PhysicalKeySerial
from digitalio import DigitalInOut, Direction, Pull


class Button:

    def __init__(self, pkey_serial: PhysicalKeySerial, gp_pin):
        self._pkey_serial = pkey_serial
        self._digital_input = DigitalInOut(gp_pin)
        self._digital_input.direction = Direction.INPUT
        self._digital_input.pull = Pull.UP

    @property
    def pkey_serial(self) -> PhysicalKeySerial:
        return self._pkey_serial

    def is_pressed(self) -> bool:
        return not self._digital_input.value