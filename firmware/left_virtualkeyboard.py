from __future__ import annotations

from both_base import TimeInMs, KeyCode, VirtualKeySerial, LayerID
from both_keyboardhalf import VKeyPressEvent
from left_reactions import KeyCmdKind, KeyCmd, OneKeyReactions, ReactionCmd, ReactionCommands

try:
    from typing import Iterator
except ImportError:
    pass


class TapHoldDecision:  # enum
    TAP = 1
    HOLD = 2


class Layer:

    def __init__(self, layer_id: LayerID, key_mapping: dict):  # dict[VirtualKeySerial, OneKeyReactions]
        self.id = layer_id
        self.key_mapping = key_mapping


class VirtualKey:

    def __init__(self, serial: VirtualKeySerial):
        # public
        self.serial = serial
        self.last_real_press_time: TimeInMs = -1

    def exist_hold_variant(self, cur_layer: Layer) -> bool:
        raise NotImplementedError()


class SimpleKey(VirtualKey):

    def exist_hold_variant(self, cur_layer: Layer) -> bool:
        return False


class TapHoldKey(VirtualKey):
    TAP_HOLD_TERM = 200  # ms


class ModKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, mod_key_code: KeyCode):
        super().__init__(serial=serial)
        self._mod_key_code = mod_key_code

    @property
    def mod_key_code(self) -> KeyCode:
        return self._mod_key_code

    def exist_hold_variant(self, cur_layer: Layer) -> bool:
        one_key_reaction = cur_layer.key_mapping[self.serial]
        return 'mouse' not in one_key_reaction.reaction_name.lower()  # mouse button keys have no hold-variant


class LayerKey(TapHoldKey):

    def __init__(self, serial: VirtualKeySerial, layer: Layer):
        super().__init__(serial=serial)

        # public
        self.layer = layer

    def exist_hold_variant(self, cur_layer: Layer) -> bool:
        return True


class PressedKeyInfo:

    def __init__(self, tap_hold_decision: TapHoldDecision, tap_reactions: OneKeyReactions | None):
        self.tap_hold_decision=tap_hold_decision
        self.tap_reactions=tap_reactions


class VirtualKeyboard:

    def __init__(self, simple_keys: list[SimpleKey], mod_keys: list[ModKey], layer_keys: list[LayerKey],
                 default_layer: Layer):
        self._all_keys = {key.serial: key for key in simple_keys + mod_keys + layer_keys}
        self._default_layer = default_layer

        self._cur_layer = default_layer
        self._deferred_keys: list[VirtualKey] = []  # keys waiting for pressing
        self._pressed_keys_info: dict[VirtualKeySerial, PressedKeyInfo] = {}
        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, vkey_events: list[VKeyPressEvent]) -> Iterator[ReactionCmd]:
        if len(vkey_events) == 0 and (self._next_decision_time is None or self._next_decision_time > time):
            return  # too early

        yield from self._update_deferred_keys(time, release_key=None)

        for vkey_event in self._sorted_vkey_events(vkey_events):
            yield from self._update_vkey_event(time, vkey_event)

        self._next_decision_time = self._calc_next_decision_time()

    def _update_deferred_keys(self, time: TimeInMs, release_key: VirtualKey | None) -> Iterator[ReactionCmd]:
        """
            tap/hold: undecided -> hold
            simple: deferred -> press
        """
        while len(self._deferred_keys) > 0:
            deferred_vkey = self._deferred_keys[0]

            decision = self._decide_deferred_key(deferred_key=deferred_vkey, time=time, release_key=release_key)
            if decision is None:
                break  # this tap/hold cannot decided => stop here

            del self._deferred_keys[0]
            if decision == TapHoldDecision.TAP:
                yield from self._start_tapping(deferred_vkey)
            else:  # HOLD
                yield from self._start_holding(deferred_vkey)

    def _decide_deferred_key(self, deferred_key: VirtualKey, time: TimeInMs, release_key: VirtualKey | None
                             ) -> TapHoldDecision | None:
        if not deferred_key.exist_hold_variant(self._cur_layer):
            return TapHoldDecision.TAP  # no hold variant

        if time - deferred_key.last_real_press_time >= TapHoldKey.TAP_HOLD_TERM:
            return TapHoldDecision.HOLD

        if release_key:
            if deferred_key.serial == release_key.serial:
                return TapHoldDecision.TAP

            if deferred_key.last_real_press_time < release_key.last_real_press_time:
                return TapHoldDecision.HOLD

        return None

    def _sorted_vkey_events(self, vkey_events: list[VKeyPressEvent]) -> Iterator[VKeyPressEvent]:
        yield from vkey_events   # todo: implement it correct

    def _update_vkey_event(self, time: TimeInMs, vkey_event: VKeyPressEvent) -> Iterator[ReactionCmd]:
        vkey_serial = vkey_event.vkey_serial
        vkey = self._all_keys[vkey_serial]

        if vkey_event.pressed:
            yield from self._start_pressing(time, vkey)
        else:
            yield from self._end_pressing(time, vkey)

    def _start_pressing(self, time: TimeInMs, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        vkey.last_real_press_time = time
        if len(self._deferred_keys) > 0 or vkey.exist_hold_variant(self._cur_layer):
            self._deferred_keys.append(vkey)
        else:
            yield from self._start_tapping(vkey)

    def _start_tapping(self, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        one_key_reactions = self._cur_layer.key_mapping.get(vkey.serial)
        self._pressed_keys_info[vkey.serial] \
            = PressedKeyInfo(tap_hold_decision=TapHoldDecision.TAP,
                             tap_reactions=one_key_reactions)
        if one_key_reactions:
            yield from one_key_reactions.on_press_key_reaction_commands

    def _start_holding(self, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        self._pressed_keys_info[vkey.serial] \
            = PressedKeyInfo(tap_hold_decision=TapHoldDecision.HOLD,
                             tap_reactions=None)

        if isinstance(vkey, LayerKey):
            layer_key = vkey
            self._cur_layer = layer_key.layer
        elif isinstance(vkey, ModKey):
            mod_key = vkey
            yield KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=mod_key.mod_key_code)

    def _end_pressing(self, time: TimeInMs, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        yield from self._update_deferred_keys(time=time, release_key=vkey)

        pressed_key_info = self._pressed_keys_info[vkey.serial]
        if pressed_key_info.tap_hold_decision == TapHoldDecision.TAP:
            yield from self._end_tapping(vkey)
        else:
            yield from self._end_holding(vkey)

        if vkey.serial in self._pressed_keys_info:
            del self._pressed_keys_info[vkey.serial]

    def _end_tapping(self, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        tap_reactions = self._pressed_keys_info[vkey.serial].tap_reactions
        if tap_reactions:
            yield from tap_reactions.on_release_key_reaction_commands

    def _end_holding(self, vkey: VirtualKey) -> Iterator[ReactionCmd]:
        if isinstance(vkey, LayerKey):
            self._cur_layer = self._default_layer
        elif isinstance(vkey, ModKey):
            mod_key = vkey
            yield KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=mod_key.mod_key_code)

    def _calc_next_decision_time(self) -> TimeInMs | None:
        if len(self._deferred_keys) == 0:
            return None
        else:
            return self._deferred_keys[0].last_real_press_time + TapHoldKey.TAP_HOLD_TERM
