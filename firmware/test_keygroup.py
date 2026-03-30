import unittest

from base import TimeInMs, PhysicalKeySerial, VirtualKeySerial
from keyboardhalf import KeyGroup


PKEY_A = 1
PKEY_B = 2

VKEY_A = 1
VKEY_B = 2
VKEY_C = 3


class KeyGroupTestBase(unittest.TestCase):

    def setUp(self):
        KeyGroup.COMBO_TERM = 50
        self._key_group = self._create_key_group()
        self._pressed_pkeys: set[PhysicalKeySerial] = set()

    @staticmethod
    def _create_key_group() -> KeyGroup:
        raise NotImplementedError()

    def _step(self, time: TimeInMs,
              press: PhysicalKeySerial | None = None,
              release: PhysicalKeySerial | None = None,
              expect: list[tuple[VirtualKeySerial, bool]] | None = None
              ) -> None:
        # update keys
        self._update_pkeys(time=time, press_pkey=press, release_pkey=release)

        if expect is None:
            return  # no expect => no checks

        # check
        vkey_events = list(self._key_group.update(time=time, all_pressed_pkeys=self._pressed_pkeys))
        actual_result = [(vkey_evt.vkey_serial, vkey_evt.pressed) for vkey_evt in vkey_events]

        self.assertEqual(expect, actual_result)

    def _update_pkeys(self, time: TimeInMs,
                      press_pkey: PhysicalKeySerial | None,
                      release_pkey: PhysicalKeySerial | None
                      ) -> None:
        if press_pkey:
            self._pressed_pkeys.add(press_pkey)
        if release_pkey:
            self._pressed_pkeys.remove(release_pkey)


class KeyGroupTestSolo(KeyGroupTestBase):

    @staticmethod
    def _create_key_group() -> KeyGroup:
        return KeyGroup(vkey_map={VKEY_A: [PKEY_A]})

    def test_simple(self):
        self._step(0, press=PKEY_A, expect=[(VKEY_A, True)])
        self._step(10, release=PKEY_A, expect=[(VKEY_A, False)])


class KeyGroupTest2Combo(KeyGroupTestBase):

    @staticmethod
    def _create_key_group() -> KeyGroup:
        return KeyGroup(vkey_map={VKEY_A: [PKEY_A],
                                  VKEY_B: [PKEY_B],
                                  VKEY_C: [PKEY_A, PKEY_B]})

    def test_a_fast1(self):
        """       COMBO_TERM
        +--------------|--------------+
        |  +--------+  |              |
        |  |   a    |  |              |
        |  +--------+  |              |
        +--------------|--------------+
           |        |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(10, release=PKEY_A, expect=[(VKEY_A, True), (VKEY_A, False)])

    # def test_a_fast2(self):
    #     """       COMBO_TERM
    #     +--------------|--------------+
    #     |  +--------+  |              |
    #     |  |   a    |  |              |
    #     |  +--------+  |              |
    #     +--------------|--------------+
    #                 |
    #     This can be happen, if this ia a TapHold Key
    #     """
    #     self._step(0, press='A')
    #     self._step(10, release='A', expect={VKEY_A: '?-'})

    def test_a_slow1(self):
        """       COMBO_TERM
        +--------------|----------------+
        | +------------|---+            |
        | |    a       |   |            |
        | +------------|---+            |
        +--------------|----------------+
          |              | |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(60, expect=[(VKEY_A, True)])
        self._step(70, release=PKEY_A, expect=[(VKEY_A, False)])

    def test_a_slow2(self):
        """       COMBO_TERM
        +--------------|----------------+
        | +------------|---+            |
        | |    a       |   |            |
        | +------------|---+            |
        +--------------|----------------+
          |                |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(70, release=PKEY_A, expect=[(VKEY_A, True), (VKEY_A, False)])

    def test_a_unaware(self) -> None:
        """       COMBO_TERM
        +--------------|--------------+
        |    +----+    |              |
        |    | a  |    |              |
        |    +----+    |              |
        +--------------|--------------+
          |         |
        """
        self._step(0, press=PKEY_A)  # no update
        self._step(30, release=PKEY_A, expect=[])

    def test_abba_fast(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +----------+ |              |
        | |    a     | |              |
        | +----------+ |              |
        |   +------+   |              |
        |   |  b   |   |              |
        |   +------+   |              |
        +--------------|--------------+
          | |      | |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(10, press=PKEY_B, expect=[(VKEY_C, True)])  # reset a + b by c
        self._step(20, release=PKEY_B, expect=[(VKEY_C, False)])
        self._step(30, release=PKEY_A, expect=[])

    def test_abba_slow(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +------------|-------+      |
        | |      a     |       |      |
        | +------------|-------+      |
        |      +-------|---+          |
        |      |    b  |   |          |
        |      +-------|---+          |
        +--------------|--------------+
          |    |           |   |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(30, press=PKEY_B, expect=[(VKEY_C, True)])  # reset a + b by c
        self._step(60, release=PKEY_B, expect=[(VKEY_C, False)])
        self._step(80, release=PKEY_A, expect=[])

    def test_abba3(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +------------|---------+    |
        | |      a     |         |    |
        | +------------|---------+    |
        |              | +---+        |
        |              | | b |        |
        |              | +---+        |
        +--------------|--------------+
          |              |   |   |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(60, press=PKEY_B, expect=[(VKEY_A, True)])
        self._step(80, release=PKEY_B)
        self._step(90, release=PKEY_A,expect=[(VKEY_A, False), (VKEY_B, True), (VKEY_B, False)])

    def test_abab_fast(self):
        """       COMBO_TERM
        +--------------|--------------+
        | +-------+    |              |
        | |   a   |    |              |
        | +-------+    |              |
        |    +-------+ |              |
        |    |  b    | |              |
        |    +-------+ |              |
        +--------------|--------------+
          |  |    |  |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(10, press=PKEY_B, expect=[(VKEY_C, True)])
        self._step(20, release=PKEY_A, expect=[(VKEY_C, False)])
        self._step(30, release=PKEY_B, expect=[])

    def test_abab_slow(self):
        """       COMBO_TERM1     COMBO_TERM2
        +--------------|--------------|--------------+
        | +------------|--------------|-+            |
        | |    a       |              | |            |
        | +------------|--------------|-+            |
        |              | +------------|----+         |
        |              | |  b         |    |         |
        |              | +------------|----+         |
        +--------------|--------------|--------------+
          |              |              |  |
        """
        self._step(0, press=PKEY_A, expect=[])
        self._step(60, press=PKEY_B, expect=[(VKEY_A, True)])
        self._step(120, release=PKEY_A, expect=[(VKEY_A, False), (VKEY_B, True)])
        self._step(130, release=PKEY_B, expect=[(VKEY_B, False)])
