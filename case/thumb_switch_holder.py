import math
from typing import Iterator

from build123d import Box, Part, Pos, Rot, Sketch, Polyline, Plane, Solid, Location
from build123d import export_stl, make_face

from base import OUTPUT_DPATH, KeyboardSide
from thumb_base import SWITCH_HOLDER_BASE_SCREW_DIST
from finger_parts import SwitchPairHolderCreator, XY
from hot_swap_socket import hot_swap_socket_data


WRITE_ENABLED = True  # set this to False, if you only want to see the result


class ThumbSwitchHolderCreator(SwitchPairHolderCreator):
    SLANTED_ANGLE = 15

    def __init__(self, side: KeyboardSide):
        super().__init__()
        self._side = side

    def create(self) -> list[Solid]:
        neg_slanted_box = self._create_slanted_neg_part()
        if self._side == KeyboardSide.RIGHT:
            neg_boxes = list(self._iter_neg_boxes())
            neg_parts = neg_boxes + [neg_slanted_box]
            side_name = 'right'
        else:
            neg_parts = [neg_slanted_box]
            side_name = 'left'


        top_part = self._create_top() - neg_parts
        middle_part = self._create_middle_part() - neg_parts
        foot_part = self._create_foot() - neg_parts

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()
            
            export_stl(top_part, OUTPUT_DPATH / f'thumb-switch-holder-{side_name}-top.stl')
            export_stl(middle_part, OUTPUT_DPATH / f'thumb-switch-holder-{side_name}-middle.stl')
            export_stl(foot_part, OUTPUT_DPATH / f'thumb-switch-holder-{side_name}-foot.stl')

        return [top_part, middle_part, foot_part]

    def _iter_top_foot_conn_points(self) -> Iterator[XY]:
        yield -1, 0

    def iter_foot_base_conn_points(self) -> Iterator[XY]:
        dy = SWITCH_HOLDER_BASE_SCREW_DIST / 2
        dx = -2 if self._side == KeyboardSide.RIGHT else -1
        yield dx, dy
        yield dx, -dy

    def _iter_hot_swap_socket_studs(self) -> Iterator[Solid]:
        for stud_hole in super()._iter_hot_swap_socket_studs():
            yield Rot(Z=180) * stud_hole

    def _create_middle_profile_face(self) -> Sketch:
        """
        order of points:
               z
               |       1
               |         2
               0---------> y
               |
               4   3
        """
        angle_rad = math.radians(self.TILT_ANGLE)

        d01 = self._create_top_part_bottom_y_len()
        d12 = hot_swap_socket_data.BODY_HEIGHT + 1

        y1 = d01 * math.cos(angle_rad)
        z1 = d01 * math.sin(angle_rad)
        y2 = y1 + d12 * math.sin(angle_rad)
        z2 = z1 - d12 * math.cos(angle_rad)
        y3 = self.FOOT_Y_LEN / 2 # y1 - 4.0
        z34 = -self.MIDDLE_PART_HEIGHT_AT_CENTER

        points = [
            (0, 0),
            (y1, z1),
            (y2, z2),
            (y3, z34),
            (0, z34),
            (0, 0),
        ]
        back_half = Polyline(points)
        return make_face(Plane.YZ * back_half)

    def _create_top_part_bottom_y_len(self) -> float:
        """ s. SwitchPairHolderCreator._create_top_profile_face()
        """
        angle_rad = math.radians(self.TILT_ANGLE)
        z12 = self._square_hole_height + hot_swap_socket_data.STUDS_HEIGHT

        return self._square_hole_len + self.HOLDER_BACK_BORDER + self.HOLDER_FRONT_BORDER + z12 * math.tan(angle_rad)
    
    def _create_hot_swap_socket_location_rel_to_switch_center(self) -> Location:
        x_off = hot_swap_socket_data.X_OFFSET
        y_off = hot_swap_socket_data.Y_OFFSET
        return Rot(Z=180) * Pos(X=x_off, Y=y_off)

    def _create_slanted_neg_part(self) -> Part:
        tilt_angle_rad = math.radians(self.TILT_ANGLE)
        top_height = self._square_hole_height + hot_swap_socket_data.STUDS_HEIGHT  # height of the top part (flat)
        top_height_middle = top_height / math.cos(tilt_angle_rad)

        parts_x_len = self._square_hole_len + 2 * self.HOLDER_LEFT_RIGHT_BORDER

        # move neg box in the right bend of the top part
        return Pos(X=parts_x_len/2, Z=top_height_middle) * Rot(Y=self.SLANTED_ANGLE) * Pos(X=50) * Box(100, 100, 100)

    def _iter_neg_boxes(self) -> Iterator[Part]:
        yield self._create_neg_box(y_len=10, dx_center_box=5.5)
        yield self._create_neg_box(y_len=18, dx_center_box=3)
    
    def _create_neg_box(self, y_len: float, dx_center_box: float) -> Part:
        holder_x_len = self._square_hole_len + 2 * self.HOLDER_LEFT_RIGHT_BORDER

        z_offset = self.MIDDLE_PART_HEIGHT_AT_CENTER + self.FOOT_HEIGHT
        dx = holder_x_len / 2 - dx_center_box  # neg box distance to center of holder
        x_len = 100
        y_len = y_len
        z_len = 5

        return Pos(X=x_len/2 + dx, Z=z_len/2 - z_offset) * Box(x_len, y_len, z_len)
