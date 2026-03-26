from base import KeyCode, VirtualKeySerial
from keysdata import NO_KEY
from virtualkeyboard import SimpleKey, ModKey, LayerKey, VirtualKeyboard
from reactions import KeyCmdKind, KeyCmd, OneKeyReactions, MouseButtonCmd, MouseWheelCmd, MouseButtonCmdKind, LogCmd

try:
    from typing import Callable, Iterator, Optional
except ImportError:
    pass

from adafruit_hid.keycode import Keycode as KC
from adafruit_hid.mouse import Mouse

MacroName = str  # p.e. 'M3'
MacroDescription = str
ModKeyName = str  # p.e. 'LCtrl'
ReactionName = str  # p.e. 'a', '$', 'M5'


KEYCODES_DATA = [
    # function row on std keyboard
    [KC.ESCAPE, 'Esc', '', 'Esc', ''],
    [KC.F1, 'F1', '', 'F1', ''],
    [KC.F2, 'F2', '', 'F2', ''],
    [KC.F3, 'F3', '', 'F3', ''],
    [KC.F4, 'F4', '', 'F4', ''],
    [KC.F5, 'F5', '', 'F5', ''],
    [KC.F6, 'F6', '', 'F6', ''],
    [KC.F7, 'F7', '', 'F7', ''],
    [KC.F8, 'F8', '', 'F8', ''],
    [KC.F9, 'F9', '', 'F9', ''],
    [KC.F10, 'F10', '', 'F10', ''],
    [KC.F11, 'F11', '', 'F11', ''],
    [KC.F12, 'F12', '', 'F12', ''],

    # row 1 on std keyboard
    [KC.GRAVE_ACCENT, '`', '~', '^', '°'],
    [KC.ONE, '1', '!', '1', '!'],
    [KC.TWO, '2', '@', '2', '"'],
    [KC.THREE, '3', '#', '3', '§'],
    [KC.FOUR, '4', '$', '4', '$'],
    [KC.FIVE, '5', '%', '5', '%'],
    [KC.SIX, '6', '^', '6', '&'],
    [KC.SEVEN, '7', '&', '7', '/', '{'],
    [KC.EIGHT, '8', '*', '8', '(', '['],
    [KC.NINE, '9', '(', '9', ')', ']'],
    [KC.ZERO, '0', ')', '0', '=', '}'],
    [KC.MINUS, '-', '_', 'ß', '?', '\\'],
    [KC.EQUALS, '=', '+', '´', '`'],
    [KC.BACKSPACE, 'Backspace', '', 'Backspace', ''],

    # row 2 on std keyboard
    [KC.TAB, 'Tab', 'BackTab', 'Tab', 'BackTab'],
    # q ... p
    [KC.LEFT_BRACKET, '[', '{', 'ü', 'Ü'],
    [KC.RIGHT_BRACKET, ']', '}', '+', '*', '~'],
    [KC.ENTER, 'Enter', '', 'Enter', ''],

    # row 3 on std keyboard
    [KC.CAPS_LOCK, 'CapsLock', '', 'CapsLock', ''],
    # a ... l
    [KC.SEMICOLON, ';', ':', 'ö', 'Ö'],
    [KC.QUOTE, "'", '"', 'ä', 'Ä'],
    [KC.POUND, '#', '~', '#', "'"],

    # row 4 on std keyboard
    [KC.LEFT_SHIFT, 'LShift', '', 'LShift', ''],
    [KC.KEYPAD_BACKSLASH, '\\', '|', '<', '>', '|'],
    # y ... m
    [KC.COMMA, ',', '<', ',', ';'],
    [KC.PERIOD, '.', '>', '.', ':'],
    [KC.FORWARD_SLASH, '/', '?', '-', '_'],
    [KC.RIGHT_SHIFT, 'RShift', '', 'RShift', ''],

    # row 5 on std keyboard
    [KC.LEFT_CONTROL, 'LCtrl', '', 'LCtrl', ''],
    [KC.LEFT_GUI, 'LGui', '', 'LGui', ''],
    [KC.LEFT_ALT, 'LAlt', '', 'LAlt', ''],
    [KC.SPACE, 'Space', '', 'Space', ''],
    [KC.RIGHT_ALT, 'RAlt', '', 'RAlt', ''],
    [KC.RIGHT_GUI, 'RGui', '', 'RGui', ''],
    [KC.APPLICATION, 'Menu', '', 'Menu', ''],

    # cursor row 1 on std keyboard
    [KC.INSERT, 'Insert', '', 'Insert', ''],
    [KC.HOME, 'Home', '', 'Home', ''],
    [KC.PAGE_UP, 'PageUp', '', 'PageUp', ''],

    # cursor row 2 on std keyboard
    [KC.DELETE, 'Del', '', 'Del', ''],
    [KC.END, 'End', '', 'End', ''],
    [KC.PAGE_DOWN, 'PageDown', '', 'PageDown', ''],

    # cursor row 3 on std keyboard
    [KC.UP_ARROW, 'Up', '', 'Up', ''],

    # cursor row 4 on std keyboard
    [KC.LEFT_ARROW, 'Left', '', 'Left', ''],
    [KC.DOWN_ARROW, 'Down', '', 'Down', ''],
    [KC.RIGHT_ARROW, 'Right', '', 'Right', ''],

    # keypad row 1 on std keyboard
    [KC.KEYPAD_NUMLOCK, 'KpNumLock', '', 'KpNumLock', ''],
    [KC.KEYPAD_FORWARD_SLASH, 'Kp/', '', 'Kp/', ''],
    [KC.KEYPAD_ASTERISK, 'Kp*', '', 'Kp*', ''],
    [KC.KEYPAD_MINUS, 'Kp', '', 'Kp', ''],

    # keypad row 2 on std keyboard
    [KC.KEYPAD_SEVEN, 'Kp7', '', 'Kp7', ''],
    [KC.KEYPAD_EIGHT, 'Kp8', '', 'Kp8', ''],
    [KC.KEYPAD_NINE, 'Kp9', '', 'Kp9', ''],
    [KC.KEYPAD_PLUS, 'Kp+', '', 'Kp+', ''],

    # keypad row 3 on std keyboard
    [KC.KEYPAD_FOUR, 'Kp4', '', 'Kp4', ''],
    [KC.KEYPAD_FIVE, 'Kp5', '', 'Kp5', ''],
    [KC.KEYPAD_SIX, 'Kp6', '', 'Kp6', ''],

    # keypad row 4 on std keyboard
    [KC.KEYPAD_ONE, 'Kp1', '', 'Kp1', ''],
    [KC.KEYPAD_TWO, 'Kp2', '', 'Kp2', ''],
    [KC.KEYPAD_THREE, 'Kp3', '', 'Kp3', ''],
    [KC.KEYPAD_ENTER, 'KpEnter', '', 'KpEnter', ''],

    # keypad row 5 on std keyboard
    [KC.KEYPAD_ZERO, 'Kp0', 'KpInsert', 'Kp0', 'KpInsert'],
    [KC.KEYPAD_PERIOD, 'Kp.', 'KpDel', '', 'KpDel'],
]


class _KeyReactionData:

    def __init__(self, key_code: KeyCode, with_shift: bool, with_alt: bool = False, name: str = '???'):
        self.key_code = key_code
        self.with_shift = with_shift
        self.with_alt = with_alt
        self.name = name


class KeyboardCreator:
    _MOD_KEY_CODE_MAP={
        'LShift': KC.LEFT_SHIFT,
        'LCtrl': KC.LEFT_CONTROL,
        'LAlt': KC.LEFT_ALT,
        'LGui': KC.LEFT_GUI,
        'RShift': KC.RIGHT_SHIFT,
        'RCtrl': KC.RIGHT_CONTROL,
        'RAlt': KC.RIGHT_ALT,
        'RGui': KC.RIGHT_GUI,
    }

    def __init__(self, virtual_key_order: list[list[VirtualKeySerial]],
                 layers: dict[VirtualKeySerial, list[ReactionName]],
                 modifiers: dict[VirtualKeySerial, ModKeyName],
                 macros: dict[MacroName, MacroDescription],
                 layer_keys_without_modifiers: Optional[set[VirtualKeySerial]] = None
                 ):
        self._virtual_key_order = virtual_key_order
        self._layers = layers
        self._modifiers = modifiers
        self._macros = macros
        self._layer_keys_without_modifiers = layer_keys_without_modifiers if layer_keys_without_modifiers else set()

        self._reaction_map: dict[ReactionName, _KeyReactionData] = {}

    def create(self) -> VirtualKeyboard:
        self._reaction_map = dict(self._create_reaction_map())

        all_vkey_serials = {vkey_serial
                            for vkey_row in self._virtual_key_order
                            for vkey_serial in vkey_row}

        simple_key_serials = all_vkey_serials - set(self._modifiers.keys()) - set(self._layers.keys())

        simple_keys = [self._create_simple_key(vkey_serial)
                       for vkey_serial in simple_key_serials]
        mod_keys = [self._create_mod_key(vkey_serial, mod_key_name)
                    for vkey_serial, mod_key_name in self._modifiers.items()]
        layer_keys = [self._create_layer_key(vkey_serial, lines,
                                             with_modifiers=vkey_serial not in self._layer_keys_without_modifiers)
                      for vkey_serial, lines in self._layers.items() if vkey_serial != NO_KEY]

        return VirtualKeyboard(
            simple_keys=simple_keys,
            mod_keys= mod_keys,
            layer_keys=layer_keys,
            default_layer=dict(self._create_layer(self._layers[NO_KEY])),
        )

    def create_key_code_map(self) -> dict[KeyCode, str]:
        key_code_map: dict[KeyCode, str] = {}
        for reaction_name, reaction_data in self._create_reaction_map():
            if not reaction_data.with_shift and not reaction_data.with_alt:
                key_code_map[reaction_data.key_code] = reaction_name
        return key_code_map

    def create_reaction_map(self) -> dict[ReactionName, _KeyReactionData]:
        return dict(self._create_reaction_map())

    @staticmethod
    def _create_reaction_map() -> Iterator[tuple[ReactionName, _KeyReactionData]]:
        for data in KEYCODES_DATA:
            key_code, en_reaction_without_shift, en_reaction_with_shift, de_reaction_without_shift, de_reaction_with_shift = data[:5]

            yield de_reaction_without_shift, _KeyReactionData(key_code=key_code, with_shift=False, name=de_reaction_without_shift)

            if de_reaction_with_shift != '':
                yield de_reaction_with_shift, _KeyReactionData(key_code=key_code, with_shift=True, name=de_reaction_with_shift)

            if len(data) >= 6:
                de_reaction_with_alt = data[5]
                yield de_reaction_with_alt, _KeyReactionData(key_code=key_code, with_shift=False, with_alt=True, name=de_reaction_with_alt)

        for i in range(26):
            key_code = KC.A + i
            en_lower_char = chr(ord('a') + i)
            en_upper_char = chr(ord('A') + i)

            if en_lower_char == 'y':
                de_lower_char = 'z'
                de_upper_char = 'Z'
            elif en_lower_char == 'z':
                de_lower_char = 'y'
                de_upper_char = 'Y'
            else:
                de_lower_char = en_lower_char
                de_upper_char = en_upper_char

            yield de_lower_char, _KeyReactionData(key_code=key_code, with_shift=False, name=de_lower_char)
            yield de_upper_char, _KeyReactionData(key_code=key_code, with_shift=True, name=de_upper_char)

            if de_lower_char == 'q':
                yield '@', _KeyReactionData(key_code=key_code, with_shift=False, with_alt=True, name='@')

    @staticmethod
    def _create_simple_key(vkey_serial: VirtualKeySerial) -> SimpleKey:
        return SimpleKey(vkey_serial)

    def _create_mod_key(self, vkey_serial: VirtualKeySerial, mod_key_name: ModKeyName) -> ModKey:
        mod_key_code = self._MOD_KEY_CODE_MAP[mod_key_name]

        return ModKey(vkey_serial, mod_key_code=mod_key_code)

    def _create_layer_key(self, vkey_serial: VirtualKeySerial, lines: list[str],
                          with_modifiers: bool) -> LayerKey:
        layer = dict(self._create_layer(lines))

        return LayerKey(vkey_serial, layer=layer, with_modifiers=with_modifiers)

    def _create_layer(self, lines: list[str]) -> Iterator[tuple[VirtualKeySerial, OneKeyReactions]]:
        assert len(lines) == len(self._virtual_key_order)

        for line, key_order_in_row in zip(lines, self._virtual_key_order):
            items = line.split()
            if len(items) != len(key_order_in_row):
                pass
            assert len(items) == len(key_order_in_row)

            for item, vkey_serial in zip(items, key_order_in_row):
                reaction = self._create_reaction(item)
                if reaction:
                    yield vkey_serial, reaction

    def _create_reaction(self, reaction_name: ReactionName) -> OneKeyReactions | None:
        if reaction_name == '·':
            return None  # not set

        if reaction_name in self._macros:
            macro_desc = self._macros[reaction_name]
            return self._create_macro_reaction(macro_desc)
        elif reaction_name == 'MouseLeft':
            press_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_PRESS)
            release_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_RELEASE)
            return OneKeyReactions(on_press_key_reaction_commands=[press_cmd],
                                   on_release_key_reaction_commands=[release_cmd])
        elif reaction_name == 'MouseRight':
            press_cmd = MouseButtonCmd(Mouse.RIGHT_BUTTON, kind=MouseButtonCmdKind.MOUSE_PRESS)
            release_cmd = MouseButtonCmd(Mouse.RIGHT_BUTTON, kind=MouseButtonCmdKind.MOUSE_RELEASE)
            return OneKeyReactions(on_press_key_reaction_commands=[press_cmd],
                                   on_release_key_reaction_commands=[release_cmd])
        elif reaction_name == 'MouseShiftLeft':
            mouse_press_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_PRESS)
            mouse_release_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_RELEASE)

            shift_press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)
            shift_release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)

            return OneKeyReactions(on_press_key_reaction_commands=[shift_press_cmd, mouse_press_cmd],
                                   on_release_key_reaction_commands=[mouse_release_cmd, shift_release_cmd])
        elif reaction_name == 'MouseCtrlLeft':
            mouse_press_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_PRESS)
            mouse_release_cmd = MouseButtonCmd(Mouse.LEFT_BUTTON, kind=MouseButtonCmdKind.MOUSE_RELEASE)

            ctrl_press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_CONTROL)
            ctrl_release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_CONTROL)

            return OneKeyReactions(on_press_key_reaction_commands=[ctrl_press_cmd, mouse_press_cmd],
                                   on_release_key_reaction_commands=[mouse_release_cmd, ctrl_release_cmd])
        elif reaction_name == 'MouseWheelUp':
            mouse_cmd = MouseWheelCmd(offset=1)
            return OneKeyReactions(on_press_key_reaction_commands=[mouse_cmd],
                                   on_release_key_reaction_commands=[])
        elif reaction_name == 'MouseWheelDown':
            mouse_cmd = MouseWheelCmd(offset=-1)
            return OneKeyReactions(on_press_key_reaction_commands=[mouse_cmd],
                                   on_release_key_reaction_commands=[])
        elif reaction_name == 'Log':
            log_cmd = LogCmd()
            return OneKeyReactions(on_press_key_reaction_commands=[log_cmd],
                                   on_release_key_reaction_commands=[])

            reaction_data: _KeyReactionData = self._reaction_map['a']
            key_code = reaction_data.key_code
            cmd = KeyCmd(kind=KeyCmdKind.KEY_SEND, key_code=key_code)

            return OneKeyReactions(on_press_key_reaction_commands=[cmd] * 100,
                                   on_release_key_reaction_commands=[])

        if reaction_name not in self._reaction_map:
            pass

        assert reaction_name in self._reaction_map
        reaction_data: _KeyReactionData = self._reaction_map[reaction_name]
        key_code = reaction_data.key_code
        press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=key_code)
        release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=key_code)

        if reaction_data.with_shift:
            shift_press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)
            shift_release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)
            return OneKeyReactions(on_press_key_reaction_commands=[shift_press_cmd, press_cmd],
                                   on_release_key_reaction_commands=[release_cmd, shift_release_cmd])
        elif reaction_data.with_alt:
            alt_press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.RIGHT_ALT)
            alt_release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.RIGHT_ALT)
            return OneKeyReactions(on_press_key_reaction_commands=[alt_press_cmd, press_cmd],
                                   on_release_key_reaction_commands=[release_cmd, alt_release_cmd])
        else:
            return OneKeyReactions(on_press_key_reaction_commands=[press_cmd],
                                   on_release_key_reaction_commands=[release_cmd])

    def _create_macro_reaction(self, macro_desc: MacroDescription) -> OneKeyReactions:
        commands = list(self._iter_macro_commands_from_desc(macro_desc))
        return OneKeyReactions(on_press_key_reaction_commands=commands,
                               on_release_key_reaction_commands=[])

    def _iter_macro_commands_from_desc(self, macro_desc: MacroDescription) -> Iterator[KeyCmd]:
        for ch in macro_desc:
            yield from self._iter_macro_commands_from_char(ch)

    def _iter_macro_commands_from_char(self, ch: str) -> Iterator[KeyCmd]:
        assert ch in self._reaction_map
        reaction_data: _KeyReactionData = self._reaction_map[ch]

        key_code = reaction_data.key_code
        press_cmd = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=key_code)
        release_cmd = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=key_code)

        if reaction_data.with_shift:
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)
            yield press_cmd
            yield release_cmd
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)
        elif reaction_data.with_alt:
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.RIGHT_ALT)
            yield press_cmd
            yield release_cmd
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.RIGHT_ALT)
        else:
            yield press_cmd
            yield release_cmd
