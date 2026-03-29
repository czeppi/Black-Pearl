import time

try:
    from typing import Iterator
except ImportError:
    pass

import board
import busio
from digitalio import DigitalInOut

from base import TimeInMs
from keyboardhalf import VKeyPressEvent

# TRRS standard assignment (ChatGPT):
#   Tip: TX
#   Ring1: RX
#   Ring2: GND
#   Sleeve: VCC


_BAUDRATE = 115200  # must be the same for both sides

_START_BYTES = b'\x07'
_MOUSE_BYTES = b'\x02'
_KEY_EVENT_BYTES = b'\x03'


class MouseMove:

    def __init__(self, dx: int, dy: int):
        # public
        self.dx = dx
        self.dy = dy


class UartBase:

    def __init__(self, tx, rx):
        self._uart = busio.UART(tx, rx, baudrate=_BAUDRATE)

    def wait_for_start(self) -> None:
        raise NotImplementedError()

    def wait_for_start_old(self) -> None:
        while True:
            print('uart write')
            self._uart.write(_START_BYTES)

            data = self._uart.read(1)
            if data == _START_BYTES:
                print("Handshake complete!")
                return

            time.sleep(0.1)


class RightUart(UartBase):

    def wait_for_start(self) -> None:
        #self._uart.read()  # clear buffer
        time.sleep(1.0)  # give left side some time for init

    def write_mouse_move(self, dx: int, dy: int) -> None:
        print(f'write_mouse_move(dx: {type(dx)} = {dx}, dy: {type(dy)} = {dy}')
        x_bytes = dx.to_bytes(1, 'big', signed=True)
        y_bytes = dy.to_bytes(1, 'big', signed=True)
        data = _MOUSE_BYTES + x_bytes + y_bytes
        print(f'uart write {data}...')
        self._uart.write(data)

    def write_vkey_events(self, vkey_events: list[VKeyPressEvent]) -> None:
        for vkey_evt in vkey_events:
            if vkey_evt.pressed:
                signed_serial = vkey_evt.vkey_serial
            else:
                signed_serial = -vkey_evt.vkey_serial

            print(f'uart signed_serial={signed_serial}')
            vkey_bytes = signed_serial.to_bytes(1, 'big', signed=True)
            data = _KEY_EVENT_BYTES + vkey_bytes

            print(f'uart write {data}...')
            self._uart.write(data)


class LeftUart(UartBase):

    def wait_for_start(self) -> None:
        pass
        #self._uart.read()  # clear buffer
        
    def read_items(self) -> Iterator[MouseMove | VKeyPressEvent]:
        while self._uart.in_waiting > 0:
            read_1st_bytes = self._uart.read(1)
            if read_1st_bytes == _START_BYTES:
                print(f'uart 1st byte')
                continue
            elif read_1st_bytes == _MOUSE_BYTES:
                byte1, byte2 = self._uart.read(2)
                print(f'uart readd mouse: byte1={byte1}, byte2={byte2}')
                dx = byte1 if byte1 < 128 else byte1 - 256
                dy = byte2 if byte2 < 128 else byte2 - 256
                print(f'uart read mouse: dx={dx}, dy={dy}')
                yield MouseMove(-dx, -dy)
            elif read_1st_bytes == _KEY_EVENT_BYTES:
                read_bytes = self._uart.read(1)
                byte1 = read_bytes[0]
                signed_value = byte1 if byte1 < 128 else byte1 - 256
                vkey_serial = abs(signed_value)
                pressed = (signed_value > 0)
                print(f'uart read key event: {vkey_serial} {pressed}')
                yield VKeyPressEvent(vkey_serial=vkey_serial, pressed=pressed)
            else:
                print(f'uart read unknown byte: {read_1st_bytes}')
