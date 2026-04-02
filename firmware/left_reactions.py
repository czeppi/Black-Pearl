from __future__ import annotations

from both_base import KeyCode


class KeyCmdKind:  # enum
    KEY_RELEASE = 0
    KEY_PRESS = 1
    KEY_SEND = 2


class MouseButtonCmdKind:
    MOUSE_RELEASE = 0
    MOUSE_PRESS = 1
    MOUSE_CLICK = 2


KeyCmdKindValue = int


class ReactionCmd:

    def __ne__(self, other: ReactionCmd) -> bool:
        return not self == other

    def __repr__(self):
        return str(self)


class KeyCmd(ReactionCmd):

    def __init__(self, kind: KeyCmdKindValue, key_code: KeyCode):
        self.kind = kind
        self.key_code = key_code

    def __str__(self) -> str:
        if self.kind == KeyCmdKind.KEY_PRESS:
            return f'press-key-code({self.key_code})'
        elif self.kind == KeyCmdKind.KEY_RELEASE:
            return f'release-key-code({self.key_code})'
        elif self.kind == KeyCmdKind.KEY_SEND:
            return f'send-key-code({self.key_code})'
        else:
            return f'???-key-code({self.key_code})'

    def __eq__(self, other: ReactionCmd) -> bool:
        return isinstance(other, KeyCmd) and self.kind == other.kind and self.key_code == other.key_code


class MouseButtonCmd(ReactionCmd):

    def __init__(self, button_no: int, kind: MouseButtonCmdKind):
        self.button_no = button_no
        self.kind = kind

    def __str__(self) -> str:
        if self.kind == MouseButtonCmdKind.MOUSE_PRESS:
            return f'press-mouse-button({self.button_no})'
        elif self.kind == MouseButtonCmdKind.MOUSE_RELEASE:
            return f'release-mouse-button({self.button_no})'
        elif self.kind == MouseButtonCmdKind.MOUSE_CLICK:
            return f'click-mouse-button({self.button_no})'
        else:
            return f'???-mouse-button({self.button_no})'

    def __eq__(self, other: ReactionCmd) -> bool:
        return isinstance(other, MouseButtonCmd) and self.button_no == other.button_no


class MouseWheelCmd(ReactionCmd):

    def __init__(self, offset: int):
        self.offset = offset

    def __str__(self) -> str:
        return f'mouse-wheel({self.offset})'

    def __eq__(self, other: ReactionCmd) -> bool:
        return isinstance(other, MouseWheelCmd) and self.offset == other.offset


class LogCmd(ReactionCmd):

    def __init__(self):
        pass


ReactionCommands = list  # list[ReactionCmd]


class OneKeyReactions:  # KeySetting?

    def __init__(self, on_press_key_reaction_commands: ReactionCommands,
                 on_release_key_reaction_commands: ReactionCommands):
        self.on_press_key_reaction_commands = on_press_key_reaction_commands
        self.on_release_key_reaction_commands = on_release_key_reaction_commands
