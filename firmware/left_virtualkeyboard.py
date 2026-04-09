from __future__ import annotations

from dataclasses import field

from both_base import TimeInMs, KeyCode, VirtualKeySerial, LayerID
from both_keyboardhalf import VKeyPressEvent
from left_reactions import KeyCmdKind, KeyCmd, OneKeyReactions, ReactionCmd, ReactionCommands

try:
    from typing import Iterator
except ImportError:
    pass


class Layer:

    def __init__(self, layer_id: LayerID, key_mapping: dict):  # dict[VirtualKeySerial, OneKeyReactions]
        self.id = layer_id
        self.key_mapping = key_mapping


class VirtualKey:

    def __init__(self, serial: VirtualKeySerial):
        # public
        self.serial = serial
        self.last_press_time: TimeInMs = -1

    def is_tap_hold(self, cur_layer_id: LayerID) -> bool:
        raise NotImplementedError()


class SimpleKey(VirtualKey):

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)

    def is_tap_hold(self, cur_layer_id: LayerID) -> bool:
        return False


class TapHoldKey(VirtualKey):
    TAP_HOLD_TERM = 200  # ms

    def __init__(self, serial: VirtualKeySerial):
        super().__init__(serial=serial)


class ModKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, mod_key_code: KeyCode, enabled_layer_ids: set[LayerID]):
        super().__init__(serial=serial)
        self._mod_key_code = mod_key_code
        self._enabled_layer_ids = enabled_layer_ids

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code

    def is_tap_hold(self, cur_layer_id: LayerID) -> bool:
        return cur_layer_id in self._enabled_layer_ids


class LayerKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, layer: Layer,
                 with_modifiers: bool=True):
        super().__init__(serial=serial)

        # public
        self.layer = layer
        self.with_modifiers = with_modifiers

    def is_tap_hold(self, cur_layer_id: LayerID) -> bool:
        return True


class PressedKeyInfo:

    def __init__(self, key_reactions: OneKeyReactions, with_modifiers: bool):
        self.key_reactions=key_reactions
        self.with_modifiers=with_modifiers


class UndecidedTapHoldKeys:
    """ manage undecided tap hold keys

    hold: if the tap/hold key is pressed for some times (typically 200ms)
          or a simple key is pressed + released, while the tap/hold is pressed
    tap: if the tap/hold key is pressed only very short (typically <200ms)

    => press of simple keys must be deferred, while a tap/hold key is pressed
    """

    def __init__(self):
        self._tap_hold_key_map: dict[VirtualKeySerial, list[SimpleKey | ModKey]] = {}
        #self._deferred_simple_keys: list[SimpleKey] = field(default_factory=list)
        self._tap_hold_key_list: list[TapHoldKey] = []  # sort by press time

    def _check_invariants(self) -> None:
        assert set(self._tap_hold_key_map.keys()) == {tap_hold_key.serial for tap_hold_key in self._tap_hold_key_list}

    def add_tap_hold_key(self, tap_hold_key: TapHoldKey) -> None:
        if tap_hold_key.serial in self._tap_hold_key_map:
            return

        self._tap_hold_key_map[tap_hold_key.serial] = []
        self._tap_hold_key_list.append(tap_hold_key)

    def add_simple_key(self, simple_key: SimpleKey | ModKey) -> None:
        """ add to the last pressed tap_hold_key, if any exists
        """
        if len(self._tap_hold_key_list) == 0:
            return

        last_tap_hold_key = self._tap_hold_key_list[-1]
        self._tap_hold_key_map[last_tap_hold_key.serial].append(simple_key)

    def remove_tap_hold_key(self, tap_hold_key: TapHoldKey) -> None:
        if tap_hold_key.serial in self._tap_hold_key_map:
            del self._tap_hold_key_map[tap_hold_key.serial]
            i = self._tap_hold_key_list.index(tap_hold_key)
            del self._tap_hold_key_list[i]

    def remove_simple_key(self, simple_key: SimpleKey | ModKey) -> None:
        ...

    def do_exists_undecided_tap_hold_keys(self) -> bool:
        return len(self._tap_hold_key_list) > 0

    def iter_tap_hold_keys_for_simple_key(self, simple_key: SimpleKey | ModKey) -> Iterator[TapHoldKey]:
        """ all tap_hold_keys which can be decided by the simple key
        """
        ...

    def iter_simple_keys_for_tap_hold_key(self, tap_hold_key: TapHoldKey) -> Iterator[SimpleKey | ModKey]:
        """ all simple keys, which wait for decision of the given tap_hold_key
        """
        yield from self._tap_hold_key_map.get(tap_hold_key.serial, [])


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
                    one_key_reactions = self._cur_layer.key_mapping.get(simple_key.serial)
                    if one_key_reactions:
                        self._pressed_keys_info[simple_key.serial] \
                            = PressedKeyInfo(with_modifiers=self._modifiers_enabled,
                                             key_reactions=one_key_reactions)
                        yield from one_key_reactions.on_press_key_reaction_commands
                    simple_keys_to_remove.append(simple_key)

            for simple_key in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key)

    def _update_vkey_event(self, time: TimeInMs, vkey_event: VKeyPressEvent) -> Iterator[ReactionCmd]:
        vkey_serial = vkey_event.vkey_serial
        vkey = self._all_keys[vkey_serial]

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

        if not vkey_event.pressed and vkey_serial in self._pressed_keys_info:
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
            one_key_reactions = self._cur_layer.key_mapping.get(tap_hold_key.serial)
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

                        one_key_reactions = self._cur_layer.key_mapping.get(simple_key.serial)
                        if one_key_reactions:
                            self._pressed_keys_info[simple_key.serial] \
                                = PressedKeyInfo(with_modifiers=self._modifiers_enabled,
                                                 key_reactions=one_key_reactions)
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
            one_key_reactions = self._cur_layer.key_mapping.get(simple_key.serial)
            if one_key_reactions:
                self._pressed_keys_info[simple_key.serial] \
                    = PressedKeyInfo(with_modifiers=self._modifiers_enabled,
                                     key_reactions=one_key_reactions)
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
                    one_key_reactions = self._cur_layer.key_mapping.get(simple_key2.serial)
                    if one_key_reactions:
                        self._pressed_keys_info[simple_key2.serial] \
                            = PressedKeyInfo(with_modifiers=self._modifiers_enabled,
                                             key_reactions=one_key_reactions)
                        yield from one_key_reactions.on_press_key_reaction_commands
                    simple_keys_to_remove.append(simple_key2)

            for simple_key2 in simple_keys_to_remove:
                self._deferred_simple_keys.remove(simple_key2)

        # this (simple) key:
        if simple_key in self._deferred_simple_keys:
            # simple: deferred -> press + release
            one_key_reactions = self._cur_layer.key_mapping.get(simple_key.serial)
            if one_key_reactions:
                yield from one_key_reactions.on_press_key_reaction_commands
                yield from one_key_reactions.on_release_key_reaction_commands

            self._deferred_simple_keys.remove(simple_key)
        else:
            # simple: pressed -> release
            one_key_reactions = self._pressed_keys_info[simple_key.serial].key_reactions
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
