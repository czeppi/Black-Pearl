""" Create the encoder holder for the left thumb
"""

import copy
from typing import Iterator

from build123d import Box, Cylinder, Part, Pos, Rot, Sphere, CounterBoreHole, Solid
from build123d import export_stl
from ocp_vscode import show

import data
from base import TOLERANCE, OUTPUT_DPATH
from thumb_base import THICKNESS, SWITCH_HOLDER_BASE_SCREW_DIST, SWITCH_HOLDER_BASE_SCREW


type XY = tuple[float, float]


WRITE_ENABLED = True  # set this to False, if you only want to show the result


def main():
    creator = EncoderHolderCreator()
    holder = creator.create()
    show(holder)


class EncoderHolderCreator:
    ENCODER_X_RIM = 2
    ENCODER_Y_RIM = 5
    ENCODER_BOTTOM_RIM = 2
    ENCODER_WIDTH = 17  # measured 16.8
    ENCODER_DEEP = 14.1  # measured 13.9
    ENCODER_LOWER_HALF_HEIGHT = 7.5
    ENCODER_HEIGHT = 7.5 + 8
    ENCODER_FOOT_WIDTH = 3.8  # measured with pins: 3.67 other side: 2.52
    SWITCH_HOLDER_X_LEN = 18.0  # measured: 17.9
    SWITCH_HOLDER_Y_LEN = 18.0  # s. SkeletonCreator.BASE_LEN
    SWITCH_HOLDER_HEIGHT = 4.0
    CONN_SPHERE_RADIUS = 10
    CONN_SPHERE_HANDLE_RADIUS = 6
    CONN_SPHERE_HANDLE_LEN = 10
    CONN_SPHERE_HANDLE_ANGLE = 30  # from z axis
    CONN_SPHERE_HANDLE_X_OFF = 2

    def create(self) -> Part:
        result = self._create_switch_holder_plate()
        result += self._create_encoder_body()

        result += self._create_handle()

        result -= list(self._create_encoder_neg_part())

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(result, OUTPUT_DPATH / 'encoder-holder.stl')

        return result
    
    def _create_switch_holder_plate(self) -> Part:
        # box
        x_left = self.SWITCH_HOLDER_X_LEN
        x_right = self.ENCODER_WIDTH + 2 * self.ENCODER_X_RIM
        x_len = x_left + x_right
        y_len = self.SWITCH_HOLDER_Y_LEN
        h = self.SWITCH_HOLDER_HEIGHT
        dx = x_len/2 - x_left

        box = Pos(X=dx, Z=-h/2) * Box(x_len, y_len, h)

        # heat inserter set holes
        screw_dy = SWITCH_HOLDER_BASE_SCREW_DIST / 2
        heat_inserter_hole = self._create_switch_holder_heat_inserter_hole()

        dx1 = -x_left / 2
        hole1 = Pos(X=dx1, Y=screw_dy) * copy.copy(heat_inserter_hole)
        hole2 = Pos(X=dx1, Y=-screw_dy) * copy.copy(heat_inserter_hole)
        box_with_holes = box - [hole1, hole2]

        return box_with_holes
    
    def _create_switch_holder_heat_inserter_hole(self) -> Part:
        screw = SWITCH_HOLDER_BASE_SCREW
        counter_bore_depth = 2.5

        return CounterBoreHole(radius=screw.hole_radius,
                               counter_bore_radius=screw.head_set_insert_radius,
                               counter_bore_depth=counter_bore_depth,
                               depth=counter_bore_depth + 100)
   
    def _create_encoder_body(self) -> Solid:
        x_len = self.ENCODER_WIDTH + 2 * self.ENCODER_X_RIM
        y_len = self.ENCODER_DEEP + 2 * self.ENCODER_Y_RIM
        z_len = self.ENCODER_HEIGHT

        body = Pos(X=x_len/2, Z=z_len/2) * Box(x_len, y_len, z_len)
        return body
    
    def _create_encoder_neg_part(self) -> Iterator[Solid]:
        x_off = self.ENCODER_WIDTH/2 + self.ENCODER_X_RIM

        z_off = self.ENCODER_HEIGHT
        z_len = self.ENCODER_LOWER_HALF_HEIGHT
        yield Pos(X=x_off, Z=-z_len/2 + z_off) * Box(self.ENCODER_WIDTH, self.ENCODER_DEEP, z_len)

        x_len = self.ENCODER_FOOT_WIDTH
        y_len = self.ENCODER_DEEP
        z_len = self.ENCODER_LOWER_HALF_HEIGHT + self.ENCODER_BOTTOM_RIM
        dx = self.ENCODER_FOOT_WIDTH/2 - self.ENCODER_WIDTH/2

        yield Pos(X=x_off + dx, Z=-z_len/2 + z_off) * Box(x_len, y_len, z_len)
        yield Pos(X=x_off - dx) * Box(x_len, y_len, 100)
    
    def _create_handle(self) -> Part:
        a = 50  # must only big enough

        h = self.CONN_SPHERE_HANDLE_LEN + self.CONN_SPHERE_HANDLE_RADIUS
        cyl = Pos(Z=a/2 - h) * Cylinder(radius=self.CONN_SPHERE_HANDLE_RADIUS, height=a)

        r = self.CONN_SPHERE_RADIUS
        sphere = Pos(Z=-h) * Sphere(radius=r)

        part_plus = Pos(X=self.CONN_SPHERE_HANDLE_X_OFF, Z=-self.SWITCH_HOLDER_HEIGHT) * Rot(Y=self.CONN_SPHERE_HANDLE_ANGLE) * (cyl + sphere)
        return part_plus - Pos(Z=a) * Box(2 * a, 2 * a, 2 * a)


if __name__ == '__main__':
    main()
