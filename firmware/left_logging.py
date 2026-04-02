from __future__ import annotations

import os

try:
    from typing import Iterator
except ImportError:
    pass

from both_base import TimeInMs, KeyCode, VirtualKeySerial
from both_keyboardhalf import VKeyPressEvent
from both_keysdata import VKEY_NAMES
from left_reactions import ReactionCmd, KeyCmd, KeyCmdKindValue, KeyCmdKind, MouseButtonCmd, MouseButtonCmdKind


class LogItem:
    """ !! no dataclass in circuit-python !!
    """

    def __init__(self, time_: TimeInMs, vkey_events: list[VKeyPressEvent], reaction_commands: list[ReactionCmd],
                 could_start_item: bool):
        self._time = time_
        self._vkey_events = vkey_events
        self._reaction_commands = reaction_commands
        self._could_start_item = could_start_item

    @property
    def time(self) -> TimeInMs:
        return self._time

    @property
    def vkey_events(self) -> list[VKeyPressEvent]:
        return self._vkey_events

    @property
    def reaction_commands(self) -> list[ReactionCmd]:
        return self._reaction_commands

    @property
    def could_start_item(self) -> bool:
        return self._could_start_item


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
        if len(log_item.vkey_events) > 0:
            event_str = self._create_vkey_events_str(log_item.vkey_events)
            yield f'{event_str}'

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


class EventLogger:

    def __init__(self):
        self._pressed_vkeys: set[VirtualKeySerial] = set()
        self._pressed_key_codes: set[KeyCode] = set()
        self._pressed_mouse_buttons: set[int] = set()
        self._log_items: list[LogItem] = []

    def update(self, t: TimeInMs, vkey_events: list[VKeyPressEvent], reaction_commands: list[ReactionCmd]) -> None:
        if len(vkey_events) == 0 and len(reaction_commands) == 0:
            return

        self._remove_old_log_items(t)
        could_start_item = (len(self._pressed_vkeys) == 0)
        log_item = LogItem(time_=t, vkey_events=vkey_events, reaction_commands=reaction_commands,
                           could_start_item=could_start_item)
        self._log_items.append(log_item)

        errors = list(self._iter_update_errors(vkey_events=vkey_events, reaction_commands=reaction_commands))
        if len(errors) > 0:
            # self._dump_logs(t=t, errors=errors)
            self._print_logs(errors=errors)

    def _remove_old_log_items(self, t: TimeInMs) -> None:
        min_keeping_time_in_ms = 60000
        i0 = 0
        for i, log_item in enumerate(self._log_items):
            dt = t - log_item.time
            if dt > min_keeping_time_in_ms and log_item.could_start_item:
                i0 = i

        self._log_items = self._log_items[i0:]

    def _iter_update_errors(self, vkey_events: list[VKeyPressEvent], reaction_commands: list[ReactionCmd]) -> Iterator[
        str]:
        for vkey_evt in vkey_events:
            yield from self._update_pressed_vkey(vkey_evt)

        for reaction_cmd in reaction_commands:
            if isinstance(reaction_cmd, KeyCmd):
                yield from self._update_pressed_key_code(reaction_cmd)
            elif isinstance(reaction_cmd, MouseButtonCmd):
                yield from self._update_pressed_mouse_buttons(reaction_cmd)

        if len(self._pressed_vkeys) == 0:
            if len(self._pressed_key_codes) != 0:
                yield f'no pressed vkeys but pressed key codes {self._pressed_key_codes}'
                self._pressed_key_codes.clear()
            if len(self._pressed_mouse_buttons) != 0:
                yield f'no pressed vkeys but pressed mouse buttons {self._pressed_mouse_buttons}'
                self._pressed_mouse_buttons.clear()

    def _update_pressed_vkey(self, vkey_evt: VKeyPressEvent) -> Iterator[str]:
        if vkey_evt.pressed:
            if vkey_evt.vkey_serial in self._pressed_vkeys:
                yield f'vkey {vkey_evt.vkey_serial} already pressed'
            else:
                self._pressed_vkeys.add(vkey_evt.vkey_serial)
        else:
            if vkey_evt.vkey_serial not in self._pressed_vkeys:
                yield f'release unpressed vkey {vkey_evt.vkey_serial}'
            else:
                self._pressed_vkeys.remove(vkey_evt.vkey_serial)

    def _update_pressed_key_code(self, key_cmd: KeyCmd) -> Iterator[str]:
        key_code = key_cmd.key_code
        if key_cmd.kind == KeyCmdKind.KEY_PRESS:
            if key_code in self._pressed_key_codes:
                yield f'key code {key_code} already pressed'
            else:
                self._pressed_key_codes.add(key_code)
        elif key_cmd.kind == KeyCmdKind.KEY_RELEASE:
            if key_code not in self._pressed_key_codes:
                yield f'release unpressed key code {key_code}'
            else:
                self._pressed_key_codes.remove(key_code)

    def _update_pressed_mouse_buttons(self, mouse_button_cmd: MouseButtonCmd) -> Iterator[str]:
        button_no = mouse_button_cmd.button_no
        if mouse_button_cmd.kind == MouseButtonCmdKind.MOUSE_PRESS:
            if button_no in self._pressed_mouse_buttons:
                yield f'mouse button {button_no} already pressed'
            else:
                self._pressed_mouse_buttons.add(button_no)
        elif mouse_button_cmd.kind == MouseButtonCmdKind.MOUSE_RELEASE:
            if button_no not in self._pressed_mouse_buttons:
                yield f'release already pressed mouse button {button_no}'
            else:
                self._pressed_mouse_buttons.remove(button_no)

    def _dump_logs(self, t: TimeInMs, errors: list[str]) -> None:
        log_dpath = '/logs'
        #if not self._exists_dir(log_dpath):
        #    os.mkdir(log_dpath)

        log_fpath = f'{log_dpath}/{t}.log'
        log_lines = list(self._iter_log_lines(errors))
        with open(log_fpath, 'w') as fh:
            buf = '\n'.join(log_lines)
            fh.write(buf)

    def _print_logs(self, errors: list[str]) -> None:
        for log_line in self._iter_log_lines(errors):
            print(log_line)

    def _iter_log_lines(self, errors: list[str]) -> Iterator[str]:
        for log_item in self._log_items:
            yield f'{log_item.time}: events={log_item.vkey_events}, reactions={log_item.reaction_commands}'

        for err_text in errors:
            yield f'ERR: {err_text}'

    @staticmethod
    def _exists_dir(path: str) -> bool:
        try:
            return (os.stat(path)[0] & 0x4000) != 0
        except OSError:
            return False
