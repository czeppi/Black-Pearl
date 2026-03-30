import time

import right_pmw3389
import board
from digitalio import DigitalInOut, Direction

from both_base import PhysicalKeySerial
from both_button import Button
from both_kbdlayoutdata import RIGHT_KEY_GROUPS
from both_keyboardhalf import KeyboardHalf, KeyGroup, VKeyPressEvent
from both_keysdata import *
from both_uart import UartBase

# TRRS
#
#   T R1 R2
#   S
#
#   T:  Tip,    VCC, red
#   R1: Ring1,  GND, black
#   R2: Ring2,  RX,  blue
#   S:  Sleeve, TX,  yellow

RIGHT_TX = board.GP4  # board.GP0
RIGHT_RX = None       # board.GP1


def main():
    right_kbd = RightKeyboardSide()
    right_kbd.init()
    right_kbd.main_loop()


class RightUart(UartBase):

    def wait_for_start(self) -> None:
        #self._uart.read()  # clear buffer
        time.sleep(1.0)  # give left side some time for init

    def write_mouse_move(self, dx: int, dy: int) -> None:
        print(f'write_mouse_move(dx: {type(dx)} = {dx}, dy: {type(dy)} = {dy}')
        x_bytes = dx.to_bytes(1, 'big', signed=True)
        y_bytes = dy.to_bytes(1, 'big', signed=True)
        data = self._MOUSE_BYTES + x_bytes + y_bytes
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
            data = self._KEY_EVENT_BYTES + vkey_bytes

            print(f'uart write {data}...')
            self._uart.write(data)


class TrackballSensor:
    """ PMW3389 pins: RST GND MT SS SCK MOSI MISO VIN

      RST:  -
      GND:  black
      MT:   -
      SS:   white
      SCK:  blue
      MOSI: green
      MISO: yellow
      VSYS: red
    """
    _SCK = board.GP18
    _MISO = board.GP16
    _MOSI = board.GP19
    _CS = board.GP17  # == SS
    _MT_PIN = board.A0
    _TARGET_CPI = 800

    def __init__(self):
        self._sensor = right_pmw3389.PMW3389(sck=self._SCK, mosi=self._MOSI, miso=self._MISO, cs=self._CS)
        self._mt_pin = DigitalInOut(board.A0)
        self._mt_pin.direction = Direction.INPUT

    def init_sensor(self) -> None:
        # Initialize sensor. You can specify CPI as an argument. Default CPI is 800.
        if self._sensor.begin():
            print("sensor ready")
        else:
            print("firmware upload failed")

        # Setting and getting CPI values
        self._sensor.set_CPI(self._TARGET_CPI)
        while True:
            cpi = self._sensor.get_CPI()
            print(f'cpi = {cpi}')
            if cpi == self._TARGET_CPI:
                break
            time.sleep(0.1)

    def update_sensor(self) -> tuple[int, int] | None:
        data = self._sensor.read_burst()

        # Limit values if needed
        dx = self._constrain(self._delta(data["dx"]), -127, 127)
        dy = self._constrain(self._delta(data["dy"]), -127, 127)

        # uncomment if mt_pin isn't used
        # if data["isOnSurface"] == True and data["isMotion"] and mt_pin.value == True:
        if self._mt_pin.value == 0 and (dy != 0 or dy != 0):
            #print(f'move ({dx}, {dy})')
            #mouse_device.move(-dy, -dx)  # !! swap values - only for testing !!
            return -dy, -dx

        return None

    @staticmethod
    def _constrain(val: int, min_val: int, max_val: int) -> int:
        return min(max_val, max(min_val, val))

    @staticmethod
    def _delta(value: int) -> int:
        """ Convert 16-bit unsigned value into a signed value
        """
        # Negative if MSB is 1
        if value & 0x8000:
            return -(~value & 0x7FFF)

        return value & 0x7FFF


class RightKeyboardSide:
    _BUTTON_MAP = {
        RIGHT_INDEX2_UP: board.GP2,  # blue
        RIGHT_INDEX_UP: board.GP3,  # yellow
        RIGHT_INDEX_DOWN: board.GP0,  # red  (orig GP4)
        RIGHT_INDEX2_DOWN: board.GP5,  # green
        RIGHT_MIDDLE_UP: board.GP10,  # blue
        RIGHT_MIDDLE_DOWN: board.GP11,  # yellow
        RIGHT_RING_UP: board.GP12,  # red
        RIGHT_RING_DOWN: board.GP13,  # blue
        RIGHT_PINKY_UP: board.GP14,  # red
        RIGHT_PINKY_DOWN: board.GP15,  # yellow
        RIGHT_THUMB_UP: board.GP21,  # red
        RIGHT_THUMB_DOWN: board.GP20,  # yellow
    }

    def __init__(self):
        self._trackball_sensor = TrackballSensor()
        self._uart = RightUart(tx=RIGHT_TX, rx=RIGHT_RX)
        self._buttons = [Button(pkey_serial=pkey_serial, gp_pin=gp_pin) for pkey_serial, gp_pin in self._BUTTON_MAP.items()]
        self._kbd_half = KeyboardHalf(key_groups=[KeyGroup(group_data)
                                                  for group_data in RIGHT_KEY_GROUPS])
    def init(self) -> None:
        print('init')
        self._trackball_sensor.init_sensor()
        print('init uart...')
        self._uart.wait_for_start()

    def main_loop(self) -> None:
        while True:
            t = time.monotonic() * 1000  # todo: before or after get_pressed_keys()?

            mouse_dx_dy = self._trackball_sensor.update_sensor()
            if mouse_dx_dy is not None:
                self._uart.write_mouse_move(*mouse_dx_dy)

            pressed_pkeys = self._get_pressed_pkeys()
            vkey_events = list(self._kbd_half.update(time=t, cur_pressed_pkeys=pressed_pkeys))
            if len(vkey_events) > 0:
                self._uart.write_vkey_events(vkey_events)

            time.sleep(0.01)

    def _get_pressed_pkeys(self) -> set[PhysicalKeySerial]:
        return {button.pkey_serial
                for button in self._buttons
                if button.is_pressed()}

    # def print_keyboard_info(self, virt_keyboard: VirtualKeyboard) -> None:
    #     for vkey in virt_keyboard.iter_all_virtual_keys():
    #         print(f'{vkey.serial} ({str(type(vkey))}): ')
    #         for pkey in vkey.physical_keys:
    #             print(f'- {pkey.serial} ({id(pkey)}) ({str(type(pkey))})')


if __name__ == '__main__':
    main()
