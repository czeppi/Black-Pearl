from both_keysdata import *

# following combination are possible (ChatGPT)
#
# SPI0:
# SCK : GP2, GP6, GP18   # SPI0 SC/SCK
# MOSI: GP3, GP7, GP19   # SPI0 TX
# MISO: GP0, GP4, GP16   # SPI0 RX
# CS:   GP0 - GP28
#
# SPI1:
# SCK:  GP10, GP14   # SPI1 SCK
# MOSI: GP11, GP15   # SPI1 TX
# MISO: GP8,  GP12   # SPI1 RX
# CS:   GP0 - GP28

# MOSI(TX) = Microcontroler OUT - Sensor IN
# MISO(RX) = Microcontroler IN - Sensor OUT
# TX = out
# RX = in


# following TX/RX combination are possible (ChatGPT)
#        TX               RX
# UART0  GP0, GP12, GP16  GP1, GP13, GP17
# UART1  GP4, GP8,  GP20  GP5, GP9,  GP21

# UART0:
# TX: GP0, GP12, GP16
# RX: GP1, GP13, GP17

# UART1:
# TX: GP4, GP8,  GP20?  # GP20 not in data sheet
# RX: GP5, GP9,  GP21?  # GP21 not in data sheet


LEFT_KEY_GROUPS = [
    {
        LPU: [LEFT_PINKY_UP],
        LPM: [LEFT_PINKY_UP, LEFT_PINKY_DOWN],
        LPD: [LEFT_PINKY_DOWN],
    },
    {
        LRU: [LEFT_RING_UP],
        LRM: [LEFT_RING_UP, LEFT_RING_DOWN],
        LRD: [LEFT_RING_DOWN],
    },
    {
        LMU: [LEFT_MIDDLE_UP],
        LMM: [LEFT_MIDDLE_UP, LEFT_MIDDLE_DOWN],
        LMD: [LEFT_MIDDLE_DOWN],
    },
    {
        LI1U: [LEFT_INDEX_UP],
        LI1M: [LEFT_INDEX_UP, LEFT_INDEX_DOWN],
        LI1D: [LEFT_INDEX_DOWN],
    },
    {
        LI2U: [LEFT_INDEX2_UP],
        LI2M: [LEFT_INDEX2_UP, LEFT_INDEX2_DOWN],
        LI2D: [LEFT_INDEX2_DOWN],
    },
    {
        LTU: [LEFT_THUMB_UP],
        LTM: [LEFT_THUMB_UP, LEFT_THUMB_DOWN],
        LTD: [LEFT_THUMB_DOWN],
    },
]


RIGHT_KEY_GROUPS = [
    {
        RTU: [RIGHT_THUMB_UP],
        RTM: [RIGHT_THUMB_UP, RIGHT_THUMB_DOWN],
        RTD: [RIGHT_THUMB_DOWN],
    },
    {
        RI2U: [RIGHT_INDEX2_UP],
        RI2M: [RIGHT_INDEX2_UP, RIGHT_INDEX2_DOWN],
        RI2D: [RIGHT_INDEX2_DOWN],
    },
    {
        RI1U: [RIGHT_INDEX_UP],
        RI1M: [RIGHT_INDEX_UP, RIGHT_INDEX_DOWN],
        RI1D: [RIGHT_INDEX_DOWN],
    },
    {
        RMU: [RIGHT_MIDDLE_UP],
        RMM: [RIGHT_MIDDLE_UP, RIGHT_MIDDLE_DOWN],
        RMD: [RIGHT_MIDDLE_DOWN],
    },
    {
        RRU: [RIGHT_RING_UP],
        RRM: [RIGHT_RING_UP, RIGHT_RING_DOWN],
        RRD: [RIGHT_RING_DOWN],
    },
    {
        RPU: [RIGHT_PINKY_UP],
        RPM: [RIGHT_PINKY_UP, RIGHT_PINKY_DOWN],
        RPD: [RIGHT_PINKY_DOWN],
    },
]


VIRTUAL_KEY_ORDER = [
    [LPU, LRU, LMU, LI1U, LI2U, LTU,   RTU, RI2U, RI1U, RMU, RRU, RPU],
    [LPM, LRM, LMM, LI1M, LI2M, LTM,   RTM, RI2M, RI1M, RMM, RRM, RPM],
    [LPD, LRD, LMD, LI1D, LI2D, LTD,   RTD, RI2D, RI1D, RMD, RRD, RPD],
]


LAYERS = {
    NO_KEY: [
        'q w e r t Del     Backspace z u i o p',
        'a s d f g Tab     Enter     h j k l ö',
        'y x c v b Space   Space     n m , . -',
    ],
    LTD: [
        'Esc · · · · ·  · @  " { } `',
        '·   · · · · ·  · \\ / ( ) $',
        "Log · · · · ·  · #  ' [ ] ´",
    ],
    LTM: [
        '· · · · · ·   · + 7 8 9 ü',
        '· · · · · ·   · - 4 5 6 ä',
        '· · · · · ·   0 · 1 2 3 ß',
    ],
    LTU: [
        '· MouseRight · MouseLeft      MouseCtrlLeft ·   · · · · · ü',
        '· ·          · ·              ·             ·   · · · · · ä',
        '· ·          · MouseShiftLeft ·             ·   · · · · · ß',
    ],
    RTM: [
        '· · · · · ·   · · F1 F2  F3  F4',
        '· · · · · ·   · · F5 F6  F7  F8',
        '· · · · · ·   · · F9 F10 F11 F12',
    ],
    RTD: [
        '% * < ^ | ·   · PageUp   Home Up   End   ·',
        '/ + ! = & ·   · ·        ·    ·    ·     ·',
        '· - > ? ~ ·   · PageDown Left Down Right ·',
    ],
    RTU: [
        '· · M5 M2 M4 ·   · · · · · ·',
        '· · ·  ·  M0 ·   · · · · · ·',
        '· · ·  ·  M1 ·   · · · · · ·',
    ],
}


MODIFIERS = {
    LI1U: 'LShift',
    LMU:  'LCtrl',
    LRU:  'LAlt',
    LPU:  'LGui',
    RI1U: 'LShift',
    RMU:  'LCtrl',
    RRU:  'LAlt',
    RPU:  'LGui',
}
