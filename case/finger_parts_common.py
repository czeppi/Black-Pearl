
import math
from build123d import Location, Pos, Rot

#
# all length values in this file are in mm
#

BACK_BORDER = 3.2  # 2.7 is minimum
CUT_WIDTH = 13.9
TILT_ANGLE = 15.0  # => the knick is 30 degree
LEFT_RIGHT_BORDER = 3.0


class SwitchPairHolderSwinger:
    """ create locations for a holder of a pair of switches

        the normal position is, when the crease edge is on the x axis
        and the middle of the crease edge coincident the origin

        the front/bach centered position is, when the center of the cut from the front/back swicth holder coincidents the origin.
    """

    def __init__(self):
        self._dy = BACK_BORDER + CUT_WIDTH / 2

    @property
    def normal_to_front_centered(self) -> Location:
        return Pos(Y=self._dy) * Rot(X=TILT_ANGLE)

    @property
    def front_centered_to_normal(self) -> Location:
        return Rot(X=-TILT_ANGLE) * Pos(Y=-self._dy)

    @property
    def normal_to_back_centered(self) -> Location:
        return Pos(Y=-self._dy) * Rot(X=-TILT_ANGLE)

    @property
    def back_centered_to_normal(self) -> Location:
        return Rot(X=TILT_ANGLE) * Pos(Y=self._dy)


class SwitchPairHolderFingerLocations:
    """ create location of switch pair holder between the different fingers

    the names of the positions:

        index2: index finger turned outside
        index:  normal position of the index finger 
        middle: position of the middle finger
        ring:   position of the ring finger
        pinkie: position of the pinkie
    """

    def __init__(self):
        self._index_to_index2 = self._calc_index_index2_pos()
        self._index_to_middle = self._create_location(move=(22, 7, 2.5), rotate=(-8, 0, -1))
        self._middle_to_ring = self._create_location(move=(25.2, -6.7, -2.4), rotate=(2, 0, 0))
        self._ring_to_pinkie = self._create_location(move=(33, -20, -16), rotate=(14, 30, 4))

        self._ring_move_correction = self._create_location(move=(2, -2, 0), rotate=(0, 0, 0))
        self._ring_rotate_correction = self._create_location(move=(2, -2, 0), rotate=(0, 5, 0))
        self._pinkie_rotate_correction = self._create_location(move=(0, 0, 0), rotate=(0, 0, -10))

    def _calc_index_index2_pos(self) -> Location:
        """ calculate the relative position of the index finger, if I rotate it away from the middle finger
        """
        dist_finger_root_switch_center = 85  # mm
        switch_width = 19.9
        switch_height = 20  # mm
        switch_gap = 0  # mm

        dx = (switch_width + switch_gap) / 2
        ry = dist_finger_root_switch_center - switch_height / 2

        phi_z_radian = -2 * math.atan(dx /ry)
        phi_z_degree = phi_z_radian * (180 / math.pi)

        dx = -ry * math.sin(phi_z_radian)
        dy = ry * math.cos(phi_z_radian) - ry

        print(f'index2: dx={dx}, dy={dy}, phi_z_degree={phi_z_degree}')

        swinger = SwitchPairHolderSwinger()
        return swinger.front_centered_to_normal * Pos(X=-dx, Y=dy) * Rot(Z=-phi_z_degree) * swinger.normal_to_front_centered

    def _create_location(self, move: tuple[float, float, float], rotate: tuple[float, float, float]) -> Location:
        """ rotation order: y-axis, x-axis, z-axis
        """
        dx, dy, dz = move
        rotx, roty, rotz = rotate

        swinger = SwitchPairHolderSwinger()
        return swinger.front_centered_to_normal * Pos(X=dx, Y=dy, Z=dz) * Rot(Z=rotz) * Rot(X=rotx) * Rot(Y=roty) * swinger.normal_to_front_centered

    @property
    def index(self) -> Location:
        return Pos(0, 0, 0)

    @property
    def index2(self) -> Location:
        return self._index_to_index2

    @property
    def middle(self) -> Location:
        return self._index_to_middle

    @property
    def ring(self) -> Location:
        return self._ring_move_correction * self._index_to_middle * self._middle_to_ring * self._ring_rotate_correction

    @property
    def pinkie(self) -> Location:
        return self._index_to_middle * self._middle_to_ring * self._ring_to_pinkie * self._pinkie_rotate_correction
