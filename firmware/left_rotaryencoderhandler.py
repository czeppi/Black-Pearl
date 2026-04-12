from __future__ import annotations

try:
    from typing import Iterator
except ImportError:
    pass

from adafruit_hid.keycode import Keycode as KC
from both_base import TimeInMs, KeyCode
from left_reactions import ReactionCmd, MouseWheelCmd, KeyCmd, KeyCmdKind


KeyCodeCombination = tuple  # tuple[KeyCode, ...]


class RotaryEncoderHandler:

    def __init__(self):
        self._key_code_recorder = _KeyCodeRecorder()
        self._reverse_combi_map = dict(ReverseKeyCodeCreator.iter_reverse_key_code_combinations())

    def update(self, time: TimeInMs, encoder_offset: int, mouse_dx: int, mouse_dy: int,
               vkey_reaction_commands: list[ReactionCmd]) -> Iterator[ReactionCmd]:
        self._key_code_recorder.update(time=time, mouse_move=(mouse_dx != 0 or mouse_dy != 0),
                                       vkey_reaction_commands=vkey_reaction_commands)

        if encoder_offset == 0:
            return

        key_code_combi = self._key_code_recorder.key_code_combination
        if len(key_code_combi) == 0:
            yield MouseWheelCmd(offset=encoder_offset)
        else:
            #print(f'key_code_combi={key_code_combi}, encoder_offset={encoder_offset}')

            if encoder_offset < 0:
                key_code_combi = self._reverse_combi_map.get(key_code_combi, tuple())
            commands = list(self._iter_key_commands_from_combi(key_code_combi))

            for _ in range(abs(encoder_offset)):
                yield from commands

    @staticmethod
    def _iter_key_commands_from_combi(key_code_combi: KeyCodeCombination) -> Iterator[KeyCmd]:
        for key_code in key_code_combi:
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=key_code)
        for key_code in reversed(key_code_combi):
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=key_code)


class _KeyCodeRecorder:
    _MAX_TIME_BETWEEN_KEY_COMMANDS = 2000  # in ms

    def __init__(self):
        self._last_time: TimeInMs = -1
        self._key_code_sequence: list[KeyCode] = []
        self._num_pressed_key_codes = 0

    def clear(self) -> None:
        self._key_code_sequence.clear()
        self._num_pressed_key_codes = 0

    def update(self, time: TimeInMs, mouse_move: bool,
               vkey_reaction_commands: list[ReactionCmd]) -> None:
        if mouse_move: # or time - self._last_time > self._MAX_TIME_BETWEEN_KEY_COMMANDS:
            self.clear()

        if len(vkey_reaction_commands) > 0 and self._num_pressed_key_codes == 0:
            self.clear()

        for reaction_cmd in vkey_reaction_commands:
            if isinstance(reaction_cmd, KeyCmd):
                self._update_key_cmd(key_cmd=reaction_cmd)
            else:
                self.clear()

    def _update_key_cmd(self, key_cmd: KeyCmd) -> None:
        if key_cmd.kind == KeyCmdKind.KEY_PRESS:
            self._key_code_sequence.append(key_cmd.key_code)
            self._num_pressed_key_codes += 1
        elif key_cmd.kind == KeyCmdKind.KEY_RELEASE:
            self._num_pressed_key_codes -= 1
        elif key_cmd.kind == KeyCmdKind.KEY_SEND:
            self._key_code_sequence.append(key_cmd.key_code)

    @property
    def key_code_combination(self) -> KeyCodeCombination:
        return tuple(self._key_code_sequence)


class ReverseKeyCodeCreator:

    @classmethod
    def iter_reverse_key_code_combinations(cls) -> Iterator[tuple[KeyCodeCombination, KeyCodeCombination]]:
        codes_with_poss_shift: list[KeyCode] = list(cls._iter_normal_char_key_codes_with_poss_shift())
        codes_without_poss_shift: list[KeyCode] = list(cls._iter_normal_char_key_codes_with_poss_shift())

        for key_code in codes_with_poss_shift + codes_without_poss_shift:
            yield (key_code,), (KC.BACKSPACE,)

        for key_code in codes_with_poss_shift:
            yield (KC.SHIFT, key_code), (KC.BACKSPACE,)

        for key_code1, key_code2 in cls._iter_symmetric_key_code_pairs():
            yield (key_code1,), (key_code2,)
            yield (key_code2,), (key_code1,)

        for key_combi1, key_combi2 in cls._iter_symmetric_key_combination_pairs():
            yield key_combi1, key_combi2
            yield key_combi2, key_combi1

    @staticmethod
    def _iter_normal_char_key_codes_with_poss_shift() -> Iterator[KeyCode]:
        yield from range(KC.A, KC.Z + 1)
        yield from [KC.ZERO, KC.ONE, KC.TWO, KC.THREE, KC.FOUR, KC.FIVE, KC.SIX, KC.SEVEN, KC.EIGHT, KC.NINE]
        yield from [KC.MINUS, KC.EQUALS, KC.LEFT_BRACKET, KC.RIGHT_BRACKET, KC.SEMICOLON, KC.QUOTE, KC.POUND, KC.COMMA,
                    KC.PERIOD, KC.FORWARD_SLASH, KC.KEYPAD_BACKSLASH]

    @staticmethod
    def _iter_normal_char_key_codes_without_poss_shift() -> Iterator[KeyCode]:
        yield from [KC.KEYPAD_ZERO, KC.KEYPAD_ONE, KC.KEYPAD_TWO, KC.KEYPAD_THREE, KC.KEYPAD_FOUR,
                    KC.KEYPAD_FIVE, KC.KEYPAD_SIX, KC.KEYPAD_SEVEN, KC.KEYPAD_EIGHT, KC.KEYPAD_NINE]
        yield from [KC.KEYPAD_FORWARD_SLASH, KC.KEYPAD_ASTERISK, KC.KEYPAD_MINUS, KC.KEYPAD_PERIOD]

    @staticmethod
    def _iter_symmetric_key_code_pairs() -> Iterator[tuple[KeyCode, KeyCode]]:
        yield KC.LEFT_ARROW, KC.RIGHT_ARROW
        yield KC.DOWN_ARROW, KC.UP_ARROW
        yield KC.PAGE_DOWN, KC.PAGE_UP

    @staticmethod
    def _iter_symmetric_key_combination_pairs() -> Iterator[tuple[KeyCodeCombination, KeyCodeCombination]]:
        yield (KC.LEFT_ALT, KC.DOWN_ARROW), (KC.LEFT_ALT, KC.UP_ARROW)
        yield (KC.LEFT_CONTROL, KC.DOWN_ARROW), (KC.LEFT_CONTROL, KC.UP_ARROW)
