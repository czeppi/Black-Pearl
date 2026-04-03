from __future__ import annotations

try:
    from typing import Iterator
except ImportError:
    pass

from both_base import PhysicalKeySerial, TimeInMs, VirtualKeySerial


# def main():
#     while True:
#         read_devices()
#         while queue.is_not_empty():
#             for queue_item in queue.read():
#                 _process_one_queue_item(queue_item)
#
#
# def _process_one_queue_item(queue_item):
#     vkey_events = queue_item.other_kbd_half_vkey_events
#     for vkey_evt in my_kbd_half.update(queue_item.pressed_pkeys):
#         read_devices()
#         vkey_events.append(vkey_evt)
#
#     sorted_vkey_events = sort_vkey_events(vkey_events)
#     for vkey_evt in sorted_vkey_events:
#         read_devices()
#         for key in kbd.update(vkey_evt):
#             send_key(key)


class KeyboardHalf:

    def __init__(self, key_groups: list[KeyGroup]):
        self._key_groups = key_groups

        self._prev_pressed_pkeys: set[PhysicalKeySerial] = set()
        self._next_decision_time: TimeInMs | None = None

    def update(self, time: TimeInMs, cur_pressed_pkeys: set[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        if cur_pressed_pkeys == self._prev_pressed_pkeys:
            if self._next_decision_time is None or self._next_decision_time > time:
                return  # too early
            else:
                for group in self._key_groups:
                    yield from group.update_by_time(time)
        else:
            for group in self._key_groups:
                yield from group.update(time, cur_pressed_pkeys)

            self._prev_pressed_pkeys = cur_pressed_pkeys.copy()

        self._next_decision_time = min((group.time_of_decision
                                        for group in self._key_groups
                                        if group.time_of_decision is not None),
                                       default=None)


class VKeyPressEvent:

    def __init__(self, vkey_serial: VirtualKeySerial, pressed: bool):
        # public
        self.vkey_serial = vkey_serial
        self.pressed = pressed

    def __str__(self):
        if self.pressed:
            return f'+{self.vkey_serial}'
        else:
            return f'-{self.vkey_serial}'

    def __repr__(self):
        return str(self)


class KeyGroup:
    COMBO_TERM = 100  # ms

    def __init__(self, vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]):
        # static
        self._pkeys_of_this_group = frozenset(self._iter_group_pkeys(vkey_map))
        self._vkey2pkeys = { vkey: frozenset(pkeys) for vkey, pkeys in vkey_map.items()}
        self._pkeys2vkeys = { frozenset(pkeys): vkey for vkey, pkeys in vkey_map.items()}
        self._is_vkey_part_of_bigger_one_map = self._create_is_part_of_bigger_one_map(vkey_map)

        # dynamic
        self._prev_pressed_pkeys: set[PhysicalKeySerial] = set()
        self._bound_pkeys: set[PhysicalKeySerial] = set()

        self._pressed_vkeys: set[VirtualKeySerial] = set()
        self._undecided_vkey: VirtualKeySerial | None = None  # pressed or undecided
        self._time_of_decision: TimeInMs | None = None  # if open_vkey is undecided

    @staticmethod
    def _iter_group_pkeys(vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]
                          ) -> Iterator[PhysicalKeySerial]:
        for pkeys in vkey_map.values():
            yield from pkeys

    @staticmethod
    def _create_is_part_of_bigger_one_map(vkey_map: dict[VirtualKeySerial, list[PhysicalKeySerial]]
                                          ) -> dict[VirtualKeySerial, bool]:
        vkey2pkeys = {vkey: frozenset(pkey_list) for vkey, pkey_list in vkey_map.items()}
        return {
            vkey: any(pkeys_set < other_set for other_set in vkey2pkeys.values())
            for vkey, pkeys_set in vkey2pkeys.items()
        }

    @property
    def time_of_decision(self) -> TimeInMs | None:
        return self._time_of_decision

    def update(self, time: TimeInMs, all_pressed_pkeys: set[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        """
            all_pressed_pkeys: this can contain pkeys of other groups
        """
        cur_pressed_pkeys = frozenset(all_pressed_pkeys & self._pkeys_of_this_group)

        if cur_pressed_pkeys == self._prev_pressed_pkeys:
            yield from self.update_by_time(time)

        else:  # pressed pkeys has changed
            if self._prev_pressed_pkeys < cur_pressed_pkeys:
                yield from self._update_with_press(time, cur_pressed_pkeys)
            elif cur_pressed_pkeys < self._prev_pressed_pkeys:
                yield from self._update_with_release(time, cur_pressed_pkeys)
            else:
                yield from self._update_with_press_and_release(time, cur_pressed_pkeys)

            self._prev_pressed_pkeys = cur_pressed_pkeys

    def update_by_time(self, time: TimeInMs) -> Iterator[VKeyPressEvent]:
        if self._time_of_decision is None or time < self._time_of_decision:
            return  # too early

        # decided: press now
        if self._undecided_vkey is None:
            self._time_of_decision = None  # ERROR => fix it
            return

        yield VKeyPressEvent(self._undecided_vkey, pressed=True)
        self._bound_pkeys |= self._vkey2pkeys[self._undecided_vkey]
        self._pressed_vkeys.add(self._undecided_vkey)
        self._undecided_vkey = None
        self._time_of_decision = None

    def _update_with_press(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]) -> Iterator[VKeyPressEvent]:
        # undecided timed out?
        yield from self.update_by_time(time)

        unbound_pressed_pkeys = frozenset(cur_pressed_pkeys - self._bound_pkeys)

        vkey_serial = self._pkeys2vkeys.get(unbound_pressed_pkeys)  # !! only recognize one vkey-press at a time !!
        if vkey_serial is None:
            self._undecided_vkey = None
            self._time_of_decision = None
            return

        if self._is_vkey_part_of_bigger_one_map.get(vkey_serial, False):
            # undecided
            self._undecided_vkey = vkey_serial
            self._time_of_decision = time + self.COMBO_TERM
        else:
            # press detected
            yield VKeyPressEvent(vkey_serial=vkey_serial, pressed=True)
            self._bound_pkeys |= unbound_pressed_pkeys
            self._pressed_vkeys.add(vkey_serial)
            self._undecided_vkey = None
            self._time_of_decision = None

    def _update_with_release(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]
                             ) -> Iterator[VKeyPressEvent]:
        released_pkeys = self._prev_pressed_pkeys - cur_pressed_pkeys

        # release pressed keys...
        for vkey_serial in self._pressed_vkeys.copy():
            pkeys = self._vkey2pkeys[vkey_serial]
            if (pkeys & released_pkeys) != frozenset():
                yield VKeyPressEvent(vkey_serial=vkey_serial, pressed=False)
                self._bound_pkeys -= self._vkey2pkeys[vkey_serial]
                self._pressed_vkeys.remove(vkey_serial)

        # release undecided key ...
        if self._undecided_vkey:
            vkey_serial = self._undecided_vkey
            pkeys = self._vkey2pkeys[vkey_serial]
            if (pkeys & released_pkeys) != frozenset():
                yield VKeyPressEvent(vkey_serial=vkey_serial, pressed=True)
                yield VKeyPressEvent(vkey_serial=vkey_serial, pressed=False)
                self._undecided_vkey = None
                self._time_of_decision = None
            else:
                yield from self.update_by_time(time)

    def _update_with_press_and_release(self, time: TimeInMs, cur_pressed_pkeys: frozenset[PhysicalKeySerial]
                                       ) -> Iterator[VKeyPressEvent]:
        """ This is VERY unusual - the reaction can change later maybe
        """
        yield from self._update_with_release(time, cur_pressed_pkeys)
        yield from self._update_with_press(time, cur_pressed_pkeys)
