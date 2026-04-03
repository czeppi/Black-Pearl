from __future__ import annotations

from both_base import TimeInMs, KeyCode, VirtualKeySerial
from both_keyboardhalf import VKeyPressEvent
from left_reactions import KeyCmdKind, KeyCmd, OneKeyReactions, ReactionCmd, ReactionCommands

try:
    from typing import Iterator
except ImportError:
    pass


Layer = dict  # dict[VirtualKeySerial, OneKeyReactions]


class VirtualKey:

    def __init__(self, serial: VirtualKeySerial):
        # public
        self.serial = serial
        self.last_press_time: TimeInMs = -1


class SimpleKey(VirtualKey):

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class TapHoldKey(VirtualKey):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class ModKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, mod_key_code: KeyCode):
        super().__init__(serial=serial)
        self._mod_key_code = mod_key_code

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code


class LayerKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, layer: Layer,
                 with_modifiers: bool=True):
        super().__init__(serial=serial)

        # public
        self.layer = layer
        self.with_modifiers = with_modifiers


class PressedKeyInfo:

    def __init__(self, key_reactions: OneKeyReactions, with_modifiers: bool):
        self.key_reactions=key_reactions
        self.with_modifiers=with_modifiers


class VirtualKeyboard:

    def __init__(self, simple_keys: list[SimpleKey], mod_keys: list[ModKey], layer_keys: list[LayerKey],
                 default_layer: Layer):
        self._all_keys = {key.serial: key for key in simple_keys + mod_keys + layer_keys}
        self._default_layer = default_layer

        self._cur_layer = default_layer
        self._modifiers_enabled = True
        self._undecided_tap_hold_keys: list[TapHoldKey] = []
        self._deferred_simple_keys: list[SimpleKey] = []  # wait for Tap/Hold decision
        self._pressed_keys_info: dict[VirtualKeySerial, PressedKeyInfo] = {}

        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, vkey_events: list[VKeyPressEvent]) -> Iterator[ReactionCmd]:
        if len(vkey_events) == 0 and (self._next_decision_time is None or self._next_decision_time > time):
            return  # too early

        yield from self._update_by_time(time)

        for vkey_event in self._sorted_vkey_events(vkey_events):
            yield from self._update_vkey_event(time, vkey_event)

        self._next_decision_time = min((vkey.last_press_time + TapHoldKey.TAP_HOLD_TERM
                                        for vkey in self._undecided_tap_hold_keys),
                                        default=None)

    def _sorted_vkey_events(self, vkey_events: list[VKeyPressEvent]) -> Iterator[VKeyPressEvent]:
        yield from vkey_events   # todo: implement it correct

    def _update_by_time(self, time: TimeInMs) -> Iterator[ReactionCmd]:
        """
            tap/hold: undecided -> hold
            simple: deferred -> press
        """
        # tap/hold: undecided -> hold
        tap_hold_key_press_times: list[TimeInMs] = []
        tap_hold_keys_to_remove: list[TapHoldKey] = []

        for tap_hold_key in self._undecided_tap_hold_keys:
            if time - tap_hold_key.last_press_time >= TapHoldKey.TAP_HOLD_TERM:
                yield from self._on_begin_holding_reaction(tap_hold_key)
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)
                tap_hold_keys_to_remove.append(tap_hold_key)

        for tap_hold_key in tap_hold_keys_to_remove:
            self._undecided_tap_hold_keys.remove(tap_hold_key)

        # simple: deferred -> press
        if len(tap_hold_key_press_times) > 0:
            oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)
            simple_keys_to_remove: list[SimpleKey] = []

            for simple_key in self._deferred_simple_keys:
                if simple_key.last_press_time > oldest_tap_hold_key_press_time:
                    one_key_reactions = self._pressed_keys_info[simple_key.serial].key_reactions
                    if one_key_reactions:
                        yield from one_key_reactions.on_press_key_reaction_commands
                    simple_keys_to_remove.append(simple_key)

            for simple_key in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key)

    def _update_vkey_event(self, time: TimeInMs, vkey_event: VKeyPressEvent) -> Iterator[ReactionCmd]:
        vkey_serial = vkey_event.vkey_serial
        vkey = self._all_keys[vkey_serial]

        if vkey_event.pressed:
            self._pressed_keys_info[vkey_serial] = PressedKeyInfo(with_modifiers=self._modifiers_enabled,
                                                                  key_reactions=self._cur_layer.get(vkey_serial))

        if self._is_tap_hold_key(vkey):
            if vkey_event.pressed:
                self._on_begin_press_tap_hold_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_tap_hold_key(vkey)

        else:
            if vkey_event.pressed:
                yield from self._on_begin_press_simple_key(vkey)
                vkey.last_press_time = time
            else:
                yield from self._on_end_press_simple_key(vkey)

        if not vkey_event.pressed:
            del self._pressed_keys_info[vkey_serial]

    def _is_tap_hold_key(self, vkey: VirtualKey) -> bool:
        if isinstance(vkey, SimpleKey):
            return False
        elif isinstance(vkey, LayerKey):
            return True
        else:
            assert isinstance(vkey, ModKey)
            return self._modifiers_enabled

    def _on_begin_press_tap_hold_key(self, tap_hold_key: TapHoldKey) -> None:
        """
            tap/hold: inactive -> undecided
        """
        self._undecided_tap_hold_keys.append(tap_hold_key)

    def _on_end_press_tap_hold_key(self, tap_hold_key: TapHoldKey) -> Iterator[ReactionCmd]:
        """
            tap/hold: undecided -> tap (press + release) + simple: deferred -> press
                      hold -> inactive
        """
        if tap_hold_key in self._undecided_tap_hold_keys:
            tap_hold_key_press_times: list[TimeInMs] = []

            # other tap/hold: undecided -> hold
            tap_hold_keys_to_remove: list[TapHoldKey] = []

            for tap_hold_key2 in self._undecided_tap_hold_keys:
                if tap_hold_key2.serial != tap_hold_key.serial:
                    if tap_hold_key2.last_press_time < tap_hold_key.last_press_time:
                        yield from self._on_begin_holding_reaction(tap_hold_key2)
                        tap_hold_key_press_times.append(tap_hold_key2.last_press_time)
                        tap_hold_keys_to_remove.append(tap_hold_key2)

            for tap_hold_key2 in tap_hold_keys_to_remove:
                self._undecided_tap_hold_keys.remove(tap_hold_key2)

            # tap/hold: tap (press + release)
            one_key_reactions = self._pressed_keys_info[tap_hold_key.serial].key_reactions
            if one_key_reactions:
                yield from one_key_reactions.on_press_key_reaction_commands
                yield from one_key_reactions.on_release_key_reaction_commands
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)

            self._undecided_tap_hold_keys.remove(tap_hold_key)

            # simple: deferred -> press
            if len(tap_hold_key_press_times) > 0:
                simple_keys_to_remove: list[SimpleKey] = []
                oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)

                for simple_key in self._deferred_simple_keys:
                    if simple_key.last_press_time > oldest_tap_hold_key_press_time:
                        # simple: -> press
                        one_key_reactions = self._pressed_keys_info[simple_key.serial].key_reactions
                        if one_key_reactions:
                            yield from one_key_reactions.on_press_key_reaction_commands
                        simple_keys_to_remove.append(simple_key)

                for simple_key in simple_keys_to_remove:
                    self._deferred_simple_keys.remove(simple_key)

        else:  # was hold
            # tap/hold: hold -> inactive
            yield from self._on_end_holding_reaction(tap_hold_key)

    def _on_begin_press_simple_key(self, simple_key: SimpleKey) -> Iterator[ReactionCmd]:
        """
             simple: inactive -> press or deferred
        """
        if len(self._undecided_tap_hold_keys) > 0:
            # simple: -> deferred
            self._deferred_simple_keys.append(simple_key)
        else:
            # simple: -> press
            one_key_reactions = self._pressed_keys_info[simple_key.serial].key_reactions
            if one_key_reactions:
                yield from one_key_reactions.on_press_key_reaction_commands

    def _on_end_press_simple_key(self, simple_key: SimpleKey) -> Iterator[ReactionCmd]:
        """
            tap/hold: undecided -> hold   # Permissive Hold (s. https://docs.qmk.fm/tap_hold)
            simple: deferred -> press + release
                    pressed -> release
        """
        # tap/hold: undecided -> hold
        tap_hold_key_press_times: list[TimeInMs] = []
        tap_hold_keys_to_remove: list[TapHoldKey] = []

        for tap_hold_key in self._undecided_tap_hold_keys:
            if tap_hold_key.last_press_time < simple_key.last_press_time:
                yield from self._on_begin_holding_reaction(tap_hold_key)
                tap_hold_key_press_times.append(tap_hold_key.last_press_time)
                tap_hold_keys_to_remove.append(tap_hold_key)

        for tap_hold_key in tap_hold_keys_to_remove:
            self._undecided_tap_hold_keys.remove(tap_hold_key)

        # other simple keys: deferred -> press (cause tap/hold is decided now)
        if len(tap_hold_key_press_times) > 0:
            oldest_tap_hold_key_press_time = min(tap_hold_key_press_times)
            simple_keys_to_remove: list[SimpleKey] = []

            for simple_key2 in self._deferred_simple_keys:
                if simple_key2.serial == simple_key.serial:
                    continue  # this case will be later considered

                if simple_key2.last_press_time > oldest_tap_hold_key_press_time:
                    # simple: -> press
                    one_key_reactions = self._pressed_keys_info[simple_key2.serial].key_reactions
                    if one_key_reactions:
                        yield from one_key_reactions.on_press_key_reaction_commands
                    simple_keys_to_remove.append(simple_key2)

            for simple_key2 in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key2)

        # this (simple) key:
        one_key_reactions = self._pressed_keys_info[simple_key.serial].key_reactions

        if simple_key in self._deferred_simple_keys:
            # simple: deferred -> press + release
            if one_key_reactions:
                yield from one_key_reactions.on_press_key_reaction_commands
                yield from one_key_reactions.on_release_key_reaction_commands

            self._deferred_simple_keys.remove(simple_key)
        else:
            # simple: pressed -> release
            if one_key_reactions:
                yield from one_key_reactions.on_release_key_reaction_commands

    def _on_begin_holding_reaction(self, tap_hold_key: TapHoldKey) -> Iterator[ReactionCmd]:
        if isinstance(tap_hold_key, LayerKey):
            layer_key = tap_hold_key
            self._cur_layer = layer_key.layer
            self._modifiers_enabled = layer_key.with_modifiers
        elif isinstance(tap_hold_key, ModKey):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=mod_key.mod_key_code)

    def _on_end_holding_reaction(self, tap_hold_key: TapHoldKey) -> Iterator[ReactionCmd]:
        if isinstance(tap_hold_key, LayerKey):
            self._cur_layer = self._default_layer
            self._modifiers_enabled = True
        elif isinstance(tap_hold_key, ModKey):
            mod_key = tap_hold_key
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=mod_key.mod_key_code)
