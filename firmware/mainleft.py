from __future__ import annotations

from keyboardcreator import KeyboardCreator, ReactionName, _KeyReactionData
from reactions import KeyCmdKind, ReactionCommands, KeyCmd, MouseButtonCmd, MouseWheelCmd, ReactionCmd, \
    MouseButtonCmdKind, LogCmd, KeyCmdKindValue

try:
    from typing import Iterator
except ImportError:
    pass

import time
import board
import usb_hid
from digitalio import DigitalInOut, Direction, Pull
import rotaryio
from adafruit_hid.keycode import Keycode as KC
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.mouse import Mouse

from base import PhysicalKeySerial, TimeInMs, KeyCode
from button import Button
from kbdlayoutdata import LEFT_KEY_GROUPS, VIRTUAL_KEY_ORDER, LAYERS, MODIFIERS
from macrosdata import MACROS
from keyboardhalf import KeyboardHalf, KeyGroup, VKeyPressEvent
from keysdata import *
from uart import LeftUart, MouseMove


# TRRS
#
#   T R1 R2
#   S
#
#   T:  Tip,    VCC, red
#   R1: Ring1,  GND, black
#   R2: Ring2,  RX,  blue
#   S:  Sleeve, TX,  yellow


LEFT_TX = board.GP0
LEFT_RX = board.GP1


def main():
    left_kbd = LeftKeyboardSide()
    left_kbd.init()
    left_kbd.main_loop()


class RollerEncoder:

    def __init__(self, pin1, pin2):
        self._encoder = rotaryio.IncrementalEncoder(pin1, pin2)
        self._last_pos = None

    def update(self) -> int:
        pos = self._encoder.position
        if self._last_pos is None:
            self._last_pos = pos
            return 0

        if pos == self._last_pos:
            return 0

        offset = pos - self._last_pos
        self._last_pos = pos
        return offset


class LeftKeyboardSide:
    _BUTTON_MAP = {
        LEFT_INDEX_RIGHT: board.GP2,  # blue
        LEFT_INDEX_DOWN: board.GP3,  # yellow
        LEFT_INDEX_UP: board.GP4,  # red
        LEFT_MIDDLE_DOWN: board.GP10,  # blue
        LEFT_MIDDLE_UP: board.GP11,  # yellow
        LEFT_RING_DOWN: board.GP12,  # red
        LEFT_RING_UP: board.GP13,  # blue
        LEFT_PINKY_DOWN: board.GP14,  # red
        LEFT_PINKY_UP: board.GP15,  # yellow
        LEFT_THUMB_DOWN: board.GP21,  # red
        LEFT_THUMB_UP: board.GP20,  # yellowu
    }
    _ROTARY_PIN1 = board.GP16
    _ROTARY_PIN2 = board.GP17

    def __init__(self):
        self._uart = LeftUart(tx=LEFT_TX, rx=LEFT_RX)
        self._roller_encoder = RollerEncoder(self._ROTARY_PIN1, self._ROTARY_PIN2)
        self._buttons = [Button(pkey_serial=pkey_serial, gp_pin=gp_pin) for pkey_serial, gp_pin in self._BUTTON_MAP.items()]
        self._kbd_half = KeyboardHalf(key_groups=[KeyGroup(group_serial, group_data)
                                                  for group_serial, group_data in LEFT_KEY_GROUPS.items()])
        creator = KeyboardCreator(virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  )
        self._virt_keyboard = creator.create()
        self._reaction_map = creator.create_reaction_map()
        self._key_code_map = creator.create_key_code_map()

        self._kbd_device = Keyboard(usb_hid.devices)
        self._mouse_device = Mouse(usb_hid.devices)
        self._queue: list[QueueItem] = []
        self._log_items: list[LogItem] = []

    def init(self) -> None:
        print('init uart...')
        self._uart.wait_for_start()

    def main_loop(self) -> None:
        print('start main loop')
        i = 0
        while True:
            try:
                if i % 500 == 0:
                    print(i)
                self._read_devices()

                for queue_item in self._read_queue_items():
                    self._process_queue_item(queue_item)

                time.sleep(0.001)
            except Exception as err:
                print(f'ERROR : {err}')
                time.sleep(0.5)
            i += 1

    def _read_devices(self) -> None:
        t = time.monotonic() * 1000

        #print(f'_read_devices: t={t}')
        my_pressed_pkeys = self._get_pressed_pkeys()

        encoder_offset = self._roller_encoder.update()
        if encoder_offset != 0:
            print(f'encoder_offset={encoder_offset}')
            self._mouse_device.move(wheel=encoder_offset)

        mouse_dx = mouse_dy = 0
        other_vkey_events: list[VKeyPressEvent] = []
        for uart_item in self._uart.read_items():
            if isinstance(uart_item, MouseMove):
                mouse_move = uart_item
                mouse_dx += mouse_move.dx
                mouse_dy += mouse_move.dy
            elif isinstance(uart_item, VKeyPressEvent):
                vkey_evt = uart_item
                other_vkey_events.append(vkey_evt)

        queue_item = QueueItem(time=t, mouse_move=MouseMove(dx=mouse_dx, dy=mouse_dy),
                               encoder_offset=encoder_offset,
                               my_pressed_pkeys=my_pressed_pkeys,
                               other_vkey_events=other_vkey_events)
        #print(f'read_devices: {queue_item}')
        self._queue.append(queue_item)

    def _read_queue_items(self) -> Iterator[QueueItem]:
        while len(self._queue) > 0:
            queue_item = self._queue[0]
            self._queue = self._queue[1:]
            yield queue_item

    def _process_queue_item(self, queue_item: QueueItem) -> None:
        #print(f'_process_queue_item: {queue_item}')
        mouse_dx = queue_item.mouse_move.dx
        mouse_dy = queue_item.mouse_move.dy
        if mouse_dx != 0 or mouse_dy != 0:
            self._mouse_device.move(mouse_dx, mouse_dy)

        if queue_item.encoder_offset != 0:
            print(f'mouse wheel: {queue_item.encoder_offset}')
            self._mouse_device.move(wheel=queue_item.encoder_offset)

        my_vkey_events = list(self._kbd_half.update(time=queue_item.time,
                                                    cur_pressed_pkeys=queue_item.my_pressed_pkeys))
        t = time.monotonic() * 1000
        reaction_commands = list(self._virt_keyboard.update(time=t,
                                                            vkey_events=queue_item.other_vkey_events + my_vkey_events))
        for reaction_cmd in reaction_commands:
            self._send_reaction_cmd(reaction_cmd)

        if len(my_vkey_events) > 0 or len(queue_item.other_vkey_events) > 0 or len(reaction_commands) > 0:
            log_item = LogItem(time_=t, my_vkey_events=my_vkey_events, other_vkey_events=queue_item.other_vkey_events,
                               reaction_commands=reaction_commands)
            self._log_items.append(log_item)
            if len(self._log_items) > 7:
                self._log_items = self._log_items[-7:]

    def _get_pressed_pkeys(self) -> set[PhysicalKeySerial]:
        return {button.pkey_serial
                for button in self._buttons
                if button.is_pressed()}

    def _send_reaction_cmd(self, reaction_cmd: ReactionCmd) -> None:
        if isinstance(reaction_cmd, KeyCmd):
            cmd_executer = KeyCmdExecuter(self._kbd_device)
            cmd_executer.execute(reaction_cmd)
        elif isinstance(reaction_cmd, MouseButtonCmd):
            mouse_cmd = reaction_cmd
            if mouse_cmd.kind == MouseButtonCmdKind.MOUSE_PRESS:
                self._mouse_device.press(mouse_cmd.button_no)
            elif mouse_cmd.kind == MouseButtonCmdKind.MOUSE_RELEASE:
                self._mouse_device.release(mouse_cmd.button_no)
        elif isinstance(reaction_cmd, MouseWheelCmd):
            self._mouse_device.move(wheel=reaction_cmd.offset)
        elif isinstance(reaction_cmd, LogCmd):
            self._send_log_key_codes()

    def _send_log_key_codes(self):
        dumper = LogItemDumper(key_code_map=self._key_code_map)
        text = '\n' + '\n'.join(dumper.dump(log_item) for log_item in self._log_items[:-2]) + '\n'

        converter = TextToKeyCodeConverter(reaction_map=self._reaction_map)
        key_commands = list(converter.convert_text(text))

        cmd_executer = KeyCmdExecuter(self._kbd_device)
        for key_cmd in key_commands:
            cmd_executer.execute(key_cmd)


class QueueItem:

    def __init__(self, time: TimeInMs, mouse_move: MouseMove, encoder_offset: int,
                 my_pressed_pkeys: set[PhysicalKeySerial], other_vkey_events: list[VKeyPressEvent]):
        # public
        self.time = time
        self.mouse_move = mouse_move
        self.encoder_offset = encoder_offset
        self.my_pressed_pkeys = my_pressed_pkeys
        self.other_vkey_events = other_vkey_events

    def __str__(self) -> str:
        return f'QueueItem({self.time}, mouse=({self.mouse_move.dx, self.mouse_move.dy}), my-pkeys=({self.my_pressed_pkeys})), other-vkey={self.other_vkey_events})'


class LogItem:

    def __init__(self, time_: TimeInMs, my_vkey_events: list[VKeyPressEvent], other_vkey_events: list[VKeyPressEvent],
                 reaction_commands: list[ReactionCmd]):
        self._time = time_
        self._my_vkey_events = my_vkey_events
        self._other_vkey_events = other_vkey_events
        self._reaction_commands = reaction_commands

    @property
    def time(self) -> TimeInMs:
        return self._time

    @property
    def my_vkey_events(self) -> list[VKeyPressEvent]:
        return self._my_vkey_events

    @property
    def other_vkey_events(self) -> list[VKeyPressEvent]:
        return self._other_vkey_events

    @property
    def reaction_commands(self) -> list[ReactionCmd]:
        return self._reaction_commands


class LogItemDumper:

    def __init__(self, key_code_map: dict[KeyCode, str]):
        self._key_code_map = key_code_map

    def dump(self, log_item: LogItem) -> str:
        return ', '.join(self._iter_str_parts(log_item))

    def _iter_str_parts(self, log_item: LogItem) -> Iterator[str]:
        yield f'{int(log_item.time)}: '

        yield ', '.join(self._iter_vkey_parts(log_item))

        if len(log_item.reaction_commands) > 0:
            reaction_str = ', '.join(self._create_reaction_str(reaction_cmd)
                                     for reaction_cmd in log_item.reaction_commands)
            yield ' -> [' + reaction_str + ']'

    def _iter_vkey_parts(self, log_item: LogItem) -> Iterator[str]:
        if len(log_item.other_vkey_events) > 0:
            other_str = self._create_vkey_events_str(log_item.other_vkey_events)
            yield f'other={other_str}'

        if len(log_item.my_vkey_events) > 0:
            self_str = self._create_vkey_events_str(log_item.my_vkey_events)
            yield f'self={self_str}'

    def _create_vkey_events_str(self, vkey_events: list[VKeyPressEvent]) -> str:
        return '[' + ', '.join(self._create_vkey_event_str(vkey_event) for vkey_event in vkey_events) + ']'

    @staticmethod
    def _create_vkey_event_str(vkey_event: VKeyPressEvent) -> str:
        prefix = '+' if vkey_event.pressed else '-'
        vkey_name = VKEY_NAMES[vkey_event.vkey_serial].lower()
        return prefix + vkey_name

    def _create_reaction_str(self, reaction_cmd: ReactionCmd) -> str:
        if isinstance(reaction_cmd, KeyCmd):
            key_cmd = reaction_cmd
            kind_str = self._create_key_cmd_kind_str(key_cmd.kind)
            key_code_str = self._key_code_map[key_cmd.key_code]
            return f'{kind_str}{key_code_str}'
        else:
            return ''

    @staticmethod
    def _create_key_cmd_kind_str(key_cmd_kind: KeyCmdKindValue) -> str:
        if key_cmd_kind == KeyCmdKind.KEY_PRESS:
            return '+'
        elif key_cmd_kind == KeyCmdKind.KEY_RELEASE:
            return '-'
        elif key_cmd_kind == KeyCmdKind.KEY_SEND:
            return '*'
        else:
            return ''


class TextToKeyCodeConverter:

    def __init__(self, reaction_map: dict[ReactionName, _KeyReactionData]):
        self._reaction_map = reaction_map

    def convert_text(self, text: str) -> Iterator[KeyCmd]:
        for char in text:
            yield from self._convert_char(char)

    def _convert_char(self, char: str) -> Iterator[KeyCmd]:
        if char == '\n':
            yield KeyCmd(kind=KeyCmdKind.KEY_SEND, key_code=KC.ENTER)
            return

        reaction_data = self._reaction_map.get(char)
        if reaction_data is None:
            return

        if reaction_data.with_shift:
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)

        if reaction_data.with_alt:
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.RIGHT_ALT)

        yield KeyCmd(kind=KeyCmdKind.KEY_SEND, key_code=reaction_data.key_code)

        if reaction_data.with_alt:
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.RIGHT_ALT)

        if reaction_data.with_shift:
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)


class KeyCmdExecuter:

    def __init__(self, kbd_device: Keyboard):
        self._kbd_device = kbd_device

    def execute(self, key_cmd: KeyCmd) -> None:
        if key_cmd.kind == KeyCmdKind.KEY_PRESS:
            self._kbd_device.press(key_cmd.key_code)
        elif key_cmd.kind == KeyCmdKind.KEY_RELEASE:
            self._kbd_device.release(key_cmd.key_code)
        elif key_cmd.kind == KeyCmdKind.KEY_SEND:
            self._kbd_device.send(key_cmd.key_code)


if __name__ == '__main__':
    main()
