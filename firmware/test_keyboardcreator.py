import unittest

from adafruit_hid.keycode import Keycode as KC
from both_kbdlayoutdata import VIRTUAL_KEY_ORDER, LAYERS, \
    MODIFIERS
from left_keyboardcreator import KeyboardCreator
from both_keyboardhalf import VKeyPressEvent
from both_keysdata import LPU, NO_KEY, LPM
from left_reactions import KeyCmdKind, KeyCmd


MACROS = {
    'M0': 'xx',
    'M1': 'xx',
    'M2': 'xx',
    'M3': 'xx',
    'M4': 'xx',
    'M5': 'xx',
}


class KeyboardCreatorTest(unittest.TestCase):

    def test_one_simple_key(self):
        creator = KeyboardCreator(virtual_key_order=[[LPU]],
                                  layers={NO_KEY: ['a']},
                                  modifiers={},
                                  macros={},
                                  )
        keyboard = creator.create()

        vkey_event = VKeyPressEvent(vkey_serial=LPU, pressed=True)
        act_reaction_commands = list(keyboard.update(time=210, vkey_events=[vkey_event]))
        expected_reaction_commands = [KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.A)]
        self.assertEqual(expected_reaction_commands, act_reaction_commands)

    def test_with_real_layout(self):
        creator = KeyboardCreator(virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  )
        virt_keyboard = creator.create()

        vkey_event = VKeyPressEvent(vkey_serial=LPM, pressed=True)
        actual_reactions = list(virt_keyboard.update(time=210, vkey_events=[vkey_event]))   # todo: not working with 10

        expected_reactions = [KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.A)]
        self.assertEqual(expected_reactions, actual_reactions)
