import unittest

from adafruit_hid.keycode import Keycode as KC
from left_keyboardcreator import KeyboardCreator
from both_keyboardhalf import VKeyPressEvent
from both_keysdata import LPU, NO_KEY
from left_reactions import KeyCmd, KeyCmdKind


class MacrosTests(unittest.TestCase):

    def setUp(self):
        pass

    def test_simple(self):
        creator = KeyboardCreator(virtual_key_order=[[LPU]],
                                  layers={NO_KEY: ['M0']},
                                  modifiers={},
                                  macros={'M0': 'aa'},
                                  )
        keyboard = creator.create()

        vkey_event = VKeyPressEvent(vkey_serial=LPU, pressed=True)
        act_reaction_commands = list(keyboard.update(time=0, vkey_events=[vkey_event]))

        press_a = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.A)
        release_a = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.A)
        expected_reaction_commands = [press_a, release_a, press_a, release_a]

        self.assertEqual(expected_reaction_commands, act_reaction_commands)

    def test_with_shift(self):
        creator = KeyboardCreator(virtual_key_order=[[LPU]],
                                  layers={NO_KEY: ['M0']},
                                  modifiers={},
                                  macros={'M0': 'Ab'},
                                  )
        keyboard = creator.create()

        vkey_event = VKeyPressEvent(vkey_serial=LPU, pressed=True)
        act_reaction_commands = list(keyboard.update(time=0, vkey_events=[vkey_event]))

        press_a = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.A)
        release_a = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.A)
        press_b = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.B)
        release_b = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.B)
        press_shift = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)
        release_shift = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)
        expected_reaction_commands = [press_shift, press_a, release_a, release_shift, press_b, release_b]

        self.assertEqual(expected_reaction_commands, act_reaction_commands)
