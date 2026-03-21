from dataclasses import dataclass
from base import mm


@dataclass
class FlatHeadScrew:
    head_radius: float
    head_height: float
    radius: float
    head_set_insert_radius: float

    @property
    def hole_radius(self) -> float:
        return self.radius + 0.2


FLAT_HEAD_SCREW_M2 = FlatHeadScrew(
    head_radius = 2.0,  # measured 1.9
    head_height = 1.0,  # measured: 0.87
    radius = 1.0,  # measured: 0.96
    head_set_insert_radius = 1.5
)

FLAT_HEAD_SCREW_M2_5 = FlatHeadScrew(
    head_radius = 2.25,  # measured 2.13
    head_height = 1.0,  # measured: 0.87
    radius = 1.25,
    head_set_insert_radius = 1.65
)


FLAT_HEAD_SCREW_M3 = FlatHeadScrew(
    head_radius = 3.5,  # measured 3.41
    head_height = 2.6,  # measured: 2.55
    radius = 1.5,  # measured: 1.48
    head_set_insert_radius = 1.95
)


FLAT_HEAD_SCREW_M4 = FlatHeadScrew(
    head_radius = 4.0,  # measured 3.9
    head_height = 2.6,  # measured: 2.55
    radius = 2.0,  # measured: 1.92
    head_set_insert_radius = 2.8
)

FLAT_HEAD_SCREW_M5 = FlatHeadScrew(
    head_radius = 5.0,  # measured 4.9
    head_height = 2.6,  # measured: 2.55
    radius = 2.5,  # measured: 2.46
    head_set_insert_radius = 3.2  # 3.05 < x < 3.5
)


FLAT_HEAD_SCREW_M6 = FlatHeadScrew(
    head_radius = 7.3,  # measured 7.25
    head_height = 3.3,  # measured: 3.25
    radius = 3.0,
    head_set_insert_radius = 3.7  # 3.6 < x < 4.0
)


@dataclass
class HexagonScrew:
    head_radius: float
    head_height: float
    radius: float  
    head_set_insert_radius: float


HEXAGON_SCREW_M6 = HexagonScrew(
    head_radius = 5.65,     # measured 5.625
    head_height = 4.4,    # measured 4.33
    radius = 3.0,  # measure 2.94 
    head_set_insert_radius = 3.7  # 3.6 < x < 4.0  (s. FLAT_HEAD_SCREW_M6)
)


class PICO_BOARD:  # orientation: usb connection is at top
    width = 21
    length = 51
    height = 1.0  # measured: 1.03
    usb_width = 8  # centered
    usb_height = 2.8
    usb_len_over_board = 1.1  # how much longer the usb port is, than the board
    hole_distance_top = 2
    hole_distance_bottom = 2.4
    hole_distance_left = 4.8
    hole_distance_right = 4.8
    pins_height = 2.8
    pin_rows_distance = 18.1  # measured 18.07 (outer bounds)
    pcb_terminal_height = 8.6  # measured: 8.6
    pcb_terminal_width = 24.8

    @classmethod
    def get_total_height_with_feet(cls) -> mm:
        return max(cls.pins_height, cls.usb_height) + cls.height + cls.pcb_terminal_height


class TRRS_SOCKET:
    cylinder_radius = 2.5
    cylinder_length = 2
    box_height = 6.1
    box_length = 12.1
    box_width = 5.1
    cable_space = 2  # at top or bottom and at the end
