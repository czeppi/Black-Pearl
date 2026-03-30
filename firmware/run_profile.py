import cProfile
import pstats
from typing import Iterator

from both_base import TimeInMs, PhysicalKeySerial
from both_kbdlayoutdata import VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS, RIGHT_KEY_GROUPS

from left_keyboardcreator import KeyboardCreator
from both_keyboardhalf import KeyGroup, KeyboardHalf
from left_virtualkeyboard import VirtualKeyboard
from both_keysdata import LEFT_INDEX_DOWN


keyboard: VirtualKeyboard | None = None
kbd_half: KeyboardHalf | None = None


MACROS = {
    'M0': 'xx',
    'M1': 'xx',
    'M2': 'xx',
    'M3': 'xx',
    'M4': 'xx',
    'M5': 'xx',
}


def main():
    global keyboard, kbd_half

    kbd_half = KeyboardHalf(key_groups=[KeyGroup(group_data)
                                        for group_data in RIGHT_KEY_GROUPS])

    creator = KeyboardCreator(virtual_key_order=VIRTUAL_KEY_ORDER,
                              layers=LAYERS,
                              modifiers=MODIFIERS,
                              macros=MACROS,
                              )
    keyboard = creator.create()

    cProfile.run('simulate()', 'profiling_results.prof')
    p = pstats.Stats('profiling_results.prof')
    #p.strip_dirs().sort_stats('cumulative').print_stats(100)
    p.strip_dirs().sort_stats('tottime').print_stats(100)


def simulate() -> None:
    for _ in range(10000):
        for time, pressed_pkeys in iter_steps():
            vkey_events = list(kbd_half.update(time=time, cur_pressed_pkeys=pressed_pkeys))
            reaction_commands = list(keyboard.update(time=time, vkey_events=vkey_events))


def iter_steps() -> Iterator[tuple[TimeInMs, set[PhysicalKeySerial]]]:
    yield 0, {LEFT_INDEX_DOWN}
    yield 30, {LEFT_INDEX_DOWN}
    yield 60, set()


main()