import unittest

from adafruit_hid.keycode import Keycode as KC
from both_base import KeyCode, TimeInMs, VirtualKeySerial, PhysicalKeySerial
from left_keyboardcreator import KeyboardCreator
from both_keyboardhalf import VKeyPressEvent, KeyGroup, \
    KeyboardHalf
from left_logging import EventLogger
from left_virtualkeyboard import SimpleKey, TapHoldKey, ModKey, \
    VirtualKeyboard, Layer, LayerKey
from both_kbdlayoutdata import VIRTUAL_KEY_ORDER, LAYERS, MODIFIERS, LAYERS_WITHOUT_MODIFIERS
from left_reactions import KeyCmdKind, KeyCmd, ReactionCommands, OneKeyReactions
from both_keysdata import RIGHT_THUMB_DOWN, RIGHT_THUMB_UP, RTU, RTM, RTD, NO_KEY, RI1U, LRU, LTU, RPU

VKEY_A = 1
VKEY_B = 2

A_DOWN = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.A)
A_UP = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.A)
B_DOWN = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.B)
B_UP = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.B)
C_DOWN = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.C)
C_UP = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.C)
SHIFT_DOWN = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.LEFT_SHIFT)
SHIFT_UP = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.LEFT_SHIFT)
SPACE_DOWN = KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=KC.SPACE)
SPACE_UP = KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=KC.SPACE)

MACROS = {
    'M0': 'xx',
    'M1': 'xx',
    'M2': 'xx',
    'M3': 'xx',
    'M4': 'xx',
    'M5': 'xx',
}


class VirtualKeyboardTestBase(unittest.TestCase):

    def setUp(self):
        self._kbd = self._create_virtual_keyboard()
        TapHoldKey.TAP_HOLD_TERM = 200

    def _create_virtual_keyboard(self) -> VirtualKeyboard:
        raise NotImplementedError()

    @staticmethod
    def _create_key_assignment(keycode: KeyCode) -> OneKeyReactions:
        return OneKeyReactions(reaction_name=f'{keycode}',
                               on_press_key_reaction_commands=[KeyCmd(kind=KeyCmdKind.KEY_PRESS, key_code=keycode)],
                               on_release_key_reaction_commands=[KeyCmd(kind=KeyCmdKind.KEY_RELEASE, key_code=keycode)])

    def _step(self, time: TimeInMs, expected_key_seq: ReactionCommands,
              press: VirtualKeySerial | None = None, release: VirtualKeySerial | None = None) -> None:

        vkey_events: list[VKeyPressEvent] = []
        if press is not None:
            vkey_event = VKeyPressEvent(press, pressed=True)
            vkey_events.append(vkey_event)
        elif release is not None:
            vkey_event = VKeyPressEvent(release, pressed=False)
            vkey_events.append(vkey_event)

        act_reaction_commands = list(self._kbd.update(time=time, vkey_events=vkey_events))

        self.assertEqual(expected_key_seq, act_reaction_commands)


class TapKeyTest(VirtualKeyboardTestBase):

    def _create_virtual_keyboard(self) -> VirtualKeyboard:
        default_layer_id = 0
        default_layer = Layer(
            layer_id=default_layer_id,
            key_mapping={
                VKEY_A: self._create_key_assignment(KC.A),
                VKEY_B: self._create_key_assignment(KC.B),
            }
        )
        return VirtualKeyboard(simple_keys=[SimpleKey(serial=VKEY_B)],
                               mod_keys=[ModKey(serial=VKEY_A, mod_key_code=KC.LEFT_SHIFT,
                                                enabled_layer_ids={default_layer_id})],
                               layer_keys=[],
                               default_layer=default_layer)

    def test_b_solo(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        |   +--------+ |              |
        |   |   b    | |              |
        |   +--------+ |              |
        +--------------|--------------+
        =>  b
        """
        self._step(0, press=VKEY_B, expected_key_seq=[B_DOWN])
        self._step(100, release=VKEY_B, expected_key_seq=[B_UP])

    def test_aabb_fast(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |              | +----------+ |
        |              | |    b     | |
        |              | +----------+ |
        +--------------|--------------+
        =>           a   b
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(199, release=VKEY_A, expected_key_seq=[A_DOWN, A_UP])
        self._step(210, press=VKEY_B, expected_key_seq=[B_DOWN])
        self._step(220, release=VKEY_B, expected_key_seq=[B_UP])

    def test_aabb_slow(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |              |   +--------+ |
        |              |   |    b   | |
        |              |   +--------+ |
        +--------------|--------------+
        =>                 b
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, release=VKEY_A, expected_key_seq=[SHIFT_UP])
        self._step(220, press=VKEY_B, expected_key_seq=[B_DOWN])
        self._step(230, release=VKEY_B, expected_key_seq=[B_UP])

    def test_abba1(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
        =>         c
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(110, press=VKEY_B, expected_key_seq=[])
        self._step(120, release=VKEY_B, expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(199, release=VKEY_A, expected_key_seq=[SHIFT_UP])

    def test_abba2(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
        =>         c
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(110, press=VKEY_B, expected_key_seq=[])
        self._step(120, release=VKEY_B, expected_key_seq=[SHIFT_DOWN, B_DOWN, B_UP])
        self._step(201, expected_key_seq=[])
        self._step(210, release=VKEY_A, expected_key_seq=[SHIFT_UP])

    def test_abba3(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-------+      |
        | |    a       |       |      |
        | +------------|-------+      |
        |              | +---+        |
        |              | | b |        |
        |              | +---+        |
        +--------------|--------------+
        =>               c
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN])
        self._step(210, press=VKEY_B, expected_key_seq=[B_DOWN])
        self._step(220, release=VKEY_B, expected_key_seq=[B_UP])
        self._step(230, release=VKEY_A, expected_key_seq=[SHIFT_UP])

    def test_abab_fast(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +-------+    |              |
        | |   a   |    |              |
        | +-------+    |              |
        |    +-------+ |              |
        |    |  b    | |              |
        |    +-------+ |              |
        +--------------|--------------+
        =>        ab
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(110, press=VKEY_B, expected_key_seq=[])
        self._step(130, release=VKEY_A, expected_key_seq=[A_DOWN, B_DOWN, A_UP])
        self._step(140, release=VKEY_B, expected_key_seq=[B_UP])

    def test_abab_slow(self) -> None:
        """       TAPPING_TERM
        +--------------|--------------+
        | +------------|-+            |
        | |    a       | |            |
        | +------------|-+            |
        |    +---------|----+         |
        |    |  b      |    |         |
        |    +---------|----+         |
        +--------------|--------------+
        =>               c
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(110, press=VKEY_B, expected_key_seq=[])
        self._step(201, expected_key_seq=[SHIFT_DOWN, B_DOWN])
        self._step(210, release=VKEY_A, expected_key_seq=[SHIFT_UP])
        self._step(220, release=VKEY_B, expected_key_seq=[B_UP])


class SimpleLayerTest(VirtualKeyboardTestBase):

    def setUp(self):
        super().setUp()
        self._event_logger = EventLogger()

    def _create_virtual_keyboard(self) -> VirtualKeyboard:
        default_layer = Layer(
            layer_id=0,
            key_mapping={
                VKEY_A: self._create_key_assignment(KC.A),
                VKEY_B: self._create_key_assignment(KC.B),
            }
        )
        layer1 = Layer(
            layer_id=1,
            key_mapping={
                VKEY_A: default_layer.key_mapping[VKEY_A],
                VKEY_B: self._create_key_assignment(KC.C),
            }
        )
        return VirtualKeyboard(simple_keys=[SimpleKey(serial=VKEY_B)],
                               mod_keys=[],
                               layer_keys=[LayerKey(serial=VKEY_A, layer=layer1)],
                               default_layer=default_layer)

    def test_abba(self) -> None:
        """    TAPPING_TERM
        +--------|--------------+
        | +------|----+         |
        | |  a   |    |         |
        | +------|----+         |
        |        | +-------+    |
        |        | |   b   |    |
        |        | +-------+    |
        +--------|--------------+
        =>            c
        """
        self._step(0, press=VKEY_A, expected_key_seq=[])
        self._step(201, expected_key_seq=[])
        self._step(210, press=VKEY_B, expected_key_seq=[C_DOWN])
        self._step(220, release=VKEY_A, expected_key_seq=[])
        self._step(230, release=VKEY_B, expected_key_seq=[C_UP])

    def _step(self, time: TimeInMs, expected_key_seq: ReactionCommands,
              press: VirtualKeySerial | None = None, release: VirtualKeySerial | None = None) -> None:

        vkey_events: list[VKeyPressEvent] = []
        if press is not None:
            vkey_event = VKeyPressEvent(press, pressed=True)
            vkey_events.append(vkey_event)
        elif release is not None:
            vkey_event = VKeyPressEvent(release, pressed=False)
            vkey_events.append(vkey_event)

        act_reaction_commands = list(self._kbd.update(time=time, vkey_events=vkey_events))

        self._event_logger.update(t=time, vkey_events=vkey_events, reaction_commands=act_reaction_commands)

        self.assertEqual(expected_key_seq, act_reaction_commands)


class ThumbUpKeyTest(unittest.TestCase):  # keyboard with only 'thumb-up' key
    """ like real keyboard, but only with the Thumb-Up-key

        This is a simple integration test
    """

    def setUp(self):
        self._kbd_half = self._create_kbd_half()
        self._virt_keyboard = self._create_keyboard()
        self._pressed_pkeys: set[PhysicalKeySerial] = set()

        KeyGroup.COMBO_TERM = 50
        TapHoldKey.TAP_HOLD_TERM = 200

    @staticmethod
    def _create_kbd_half() -> KeyboardHalf:
        rt_group = KeyGroup({
                        RTU: [RIGHT_THUMB_UP],
                        RTM: [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
                        RTD: [RIGHT_THUMB_DOWN],
                    })
        return KeyboardHalf(key_groups=[rt_group])

    @staticmethod
    def _create_keyboard() -> VirtualKeyboard:
        key_order = [[RTU], [RTM], [RTD]]

        layers = {
            NO_KEY: ['Space', 'Backspace', 'Enter'],
            RTU: ['·', '·', '·'],
            RTD: ['·', '·', '·'],
            RTM: ['·', '·', '·'],
        }

        creator = KeyboardCreator(virtual_key_order=key_order,
                                  layers=layers,
                                  modifiers={},
                                  macros={},
                                  )
        return creator.create()

    def test_press_short1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(20, release='rtu', expected_key_seq=[SPACE_DOWN, SPACE_UP])

    def test_press_short2(self):
        self._step(00, press='rtu', expected_key_seq=[])
        self._step(10, expected_key_seq=[])
        self._step(20, release='rtu', expected_key_seq=[SPACE_DOWN, SPACE_UP])

    def test_press_longer_as_combo_term1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(70, release='rtu', expected_key_seq=[SPACE_DOWN, SPACE_UP])

    def test_press_longer_as_combo_term2(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(60, expected_key_seq=[])
        self._step(70, release='rtu', expected_key_seq=[SPACE_DOWN, SPACE_UP])

    def test_press_longer_as_hold_term1(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(300, release='rtu', expected_key_seq=[SPACE_DOWN, SPACE_UP])  # ???

    def test_press_longer_as_hold_term2(self):
        self._step(0, press='rtu', expected_key_seq=[])
        self._step(60, expected_key_seq=[])
        self._step(270, expected_key_seq=[])
        self._step(300, release='rtu', expected_key_seq=[])

    def _step(self, time: TimeInMs, expected_key_seq: ReactionCommands, press='', release=''):
        if press == 'rtu':
            self._pressed_pkeys.add(RIGHT_THUMB_UP)
        elif release == 'rtu':
            self._pressed_pkeys.remove(RIGHT_THUMB_UP)

        vkey_events = list(self._kbd_half.update(time, cur_pressed_pkeys=self._pressed_pkeys))
        act_reaction_commands = list(self._virt_keyboard.update(time=time, vkey_events=vkey_events))

        self.assertEqual(expected_key_seq, act_reaction_commands)


class RealVKeyboardTest(unittest.TestCase):

    def setUp(self):
        creator = KeyboardCreator(virtual_key_order=VIRTUAL_KEY_ORDER,
                                  layers=LAYERS,
                                  modifiers=MODIFIERS,
                                  macros=MACROS,
                                  layer_keys_without_modifiers=LAYERS_WITHOUT_MODIFIERS
                                  )
        self._virt_keyboard = creator.create()

    def test_W_correct(self):
        """
        614919:,other=[+ri1u]
        614973:,self=[+lmu]
        615043:,self=[-lmu],->[+e,-e]
        615119:,,->[+LShift]
        615149:,other=[-ri1u],->[-LShift]

        +--------------|--------------+
        | +------------|-+            |
        | |    u       | |            |
        | +------------|-+            |
        |   +------+   |              |
        |   |  w   |   |              |
        |   +------+   |              |
        +--------------|--------------+
                   |     |
                   |   -Shift
               +Shift+w-w

          +: press, -: release
        """
        press_w = KeyCmd(KeyCmdKind.KEY_PRESS, KC.W)
        release_w = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.W)
        press_shift = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_SHIFT)
        release_shift = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_SHIFT)

        self._step(19, [VKeyPressEvent(RI1U, pressed=True)], expected_reactions=[])
        self._step(73, [VKeyPressEvent(LRU, pressed=True)], expected_reactions=[])
        self._step(143, [VKeyPressEvent(LRU, pressed=False)], expected_reactions=[press_shift, press_w, release_w])
        self._step(219, [], expected_reactions=[])
        self._step(249, [VKeyPressEvent(RI1U, pressed=False)], expected_reactions=[release_shift])

    def test_ue(self):
        press_p = KeyCmd(KeyCmdKind.KEY_PRESS, KC.P)
        release_p = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.P)
        press_ue = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_BRACKET)
        release_ue = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_BRACKET)

        self._step(831, [VKeyPressEvent(LTU, pressed=True)], expected_reactions=[])
        self._step(982, [VKeyPressEvent(RPU, pressed=True), VKeyPressEvent(RPU, pressed=False)],
                   expected_reactions=[press_ue, release_ue])
        self._step(2690, [VKeyPressEvent(LTU, pressed=False)], expected_reactions=[])

        # 6=LTU, 12=RPU, 19=p, 47=ü
        # #831: +6 = >
        #982: +12, -12 = > keys: +19, -19,
        #1671: +12, -12 = > keys: +47, -47,
        #1875: +12, -12 = > keys: +47, -47,
        #2462: +12, -12 = > keys: +47, -47,
        #2690: -6 = >

    def test_lgui(self):
        """
        uart read key event: 12 True   # 12 -> RPU
        160111.250: +12 =>

        uart read key event: 12 False
        160111.938:  => keys: +227,  # 227 -> KC.LEFT_GUI

        uart read key event: 12 True
        160112.375: +12 => keys: +47,  # 47 -> KC.LEFT_BRACKET
        ERR: vkey 12 already pressed   => ???

        uart read key event: 12 False
        160112.438: -12 => keys: -47,

        uart read key event: 12 True
        160112.563: +12 => keys: +47,

        uart read key event: 12 False
        160112.625: -12 => keys: -47,
        160114.125: -6 =>
        ERR: no pressed vkeys but pressed key codes {227}


        """
        #press_ue = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_BRACKET)
        #release_ue = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_BRACKET)
        press_lgui = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_GUI)
        release_lgui = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_GUI)
        #KC.LEFT_GUI=227

        self._step(0, [VKeyPressEvent(RPU, pressed=True)], expected_reactions=[])
        self._step(300, [], expected_reactions=[press_lgui])
        self._step(500, [VKeyPressEvent(RPU, pressed=False)], expected_reactions=[release_lgui])

    def test_lgui2(self):
        press_lgui = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_GUI)
        release_lgui = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_GUI)
        self._step(0, [VKeyPressEvent(RPU, pressed=True)], expected_reactions=[])
        self._step(300, [VKeyPressEvent(RPU, pressed=False)], expected_reactions=[press_lgui, release_lgui])
        self._step(700, [VKeyPressEvent(RPU, pressed=True)], expected_reactions=[])

    def test_lgui3(self):
        press_lgui = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_GUI)
        release_lgui = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_GUI)
        self._step(0, [VKeyPressEvent(RPU, pressed=True)], expected_reactions=[])
        self._step(300, [VKeyPressEvent(RPU, pressed=False)], expected_reactions=[press_lgui, release_lgui])

    def test_lgui4(self):
        """
        266.782: +6 =>    # 6 -> LTU

        uart read key event: 12 True   # 12 -> RPU
        267.432: +12 => keys: +47,

        267.947: -6 =>

        uart read key event: 12 False
        268.209: -12 => keys: -227,
        ERR: release unpressed key code 227
        ERR: no pressed vkeys but pressed key codes {47}
        """
        press_ue = KeyCmd(KeyCmdKind.KEY_PRESS, KC.LEFT_BRACKET)
        release_ue = KeyCmd(KeyCmdKind.KEY_RELEASE, KC.LEFT_BRACKET)

        self._step(  0, [VKeyPressEvent(LTU, pressed=True)], expected_reactions=[])
        self._step(300, [VKeyPressEvent(RPU, pressed=True)], expected_reactions=[press_ue])
        self._step(600, [VKeyPressEvent(LTU, pressed=False)], expected_reactions=[])
        self._step(900, [VKeyPressEvent(RPU, pressed=False)], expected_reactions=[release_ue])

    def _step(self, time: TimeInMs, vkey_events: list[VKeyPressEvent], expected_reactions: list[KeyCmd]):
        actual_reactions = list(
            self._virt_keyboard.update(time=time, vkey_events=vkey_events))
        self.assertEqual(expected_reactions, actual_reactions)
