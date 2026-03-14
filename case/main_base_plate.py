""" Create base plate
"""

import math
from typing import Iterator
from ocp_vscode import show
from build123d import Part, Compound, Pos, Rot, Cylinder, Box, export_stl, make_face, Polyline, extrude, Plane, CounterBoreHole, Sphere, Axis, fillet, Solid

import data
from base import OUTPUT_DPATH, mm, Degree, KeyboardSide
from double_ball_join import FingerDoubleBallJoinCreator, ThumbDoubleBallJoinCreator

WRITE_ENABLED = True


type XY = tuple[float, float]


def main():
    part = CircleBasePlateCreator(KeyboardSide.LEFT).create_controller_holder()
    part = CircleBasePlateCreator(KeyboardSide.LEFT).create_trrs_stopper()
    part = create_assembly()
    show(part)


def create_assembly() -> Compound:
    creator = CircleBasePlateCreator(KeyboardSide.LEFT)
    plate = creator.create_plate()
    cover = creator.create_cover()
    return Compound(label="base", children=[plate, cover])


class CircleBasePlateCreator:
    # REL_HEIGHT = 0.75
    THICKNESS_TOP = 5
    TOP_FILLET_RADIUS = 10
    INTERIOR_HEIGHT = data.PICO_BOARD.get_total_height_with_feet() + 0.2 - 3  # => over the controller should 2mm be left
    THICKNESS_RIM = 4

    FINGER_POST_SPHERE_RADIUS = FingerDoubleBallJoinCreator.SPHERE_RADIUS
    FINGER_POST_HANDLE_RADIUS = FingerDoubleBallJoinCreator.HANDLE_RADIUS
    FINGER_POST_HANDLE_LEN = 4
    FINGER_POST_POS_ANGLE = 150  # math. in degree
    FINGER_POST_POS_DIST_FROM_BORDER = 20

    THUMB_POST_SPHERE_RADIUS = ThumbDoubleBallJoinCreator.SPHERE_RADIUS
    THUMB_POST_HANDLE_RADIUS = ThumbDoubleBallJoinCreator.HANDLE_RADIUS
    THUMB_POST_HANDLE_LEN = 4
    THUMB_POST_POS_ANGLE = -60  # math. in degree
    THUMB_POST_POS_DIST_FROM_BORDER = 20

    TRRS_SOCKET_POS_ANGLE = 180  # math. in degree
    TRRS_SOCKET_RIM = 3

    CONTROLLER_POS_ANGLE = 45  # math. in degree
    CONTROLLER_POS_DIST_FROM_CENTER = 23
    CONTROLLER_ROT_ANGLE = 45
    CONTROLLER_RIM = 2
    CONTROLLER_HOLD_SCREW = data.FLAT_HEAD_SCREW_M2
    CONTROLLER_HOLD_SCREW_HOLE_LEN = 4
    CONTROLLER_HOLD_SCREW_DIST_FROM_BOARD = 5
    CONTROLLER_USB_HOLE_WIDTH = 11.7
    CONTROLLER_USB_HOLE_HEIGHT = 8.9

    THUMB_CABEL_HOLE_POS_ANGLE = 150  # math. in degree
    THUMB_CABEL_HOLE_POS_DIST_FROM_CENTER = 5
    THUMB_CABEL_HOLE_RADIUS = 6

    FINGER_CABEL_HOLE_POS_ANGLE = -30  # math. in degree
    FINGER_CABEL_HOLE_HEIGHT = 8
    FINGER_CABEL_HOLE_WIDTH = 12
    FINGER_CABEL_ROT = 30

    COVER_RADIUS = 50
    COVER_HEIGHT = 2
    COVER_STEP_LEN = 1
    COVER_NUM_SCREWS = 2
    COVER_SCREW_START_ANGLE = 45  # math. in degree
    COVER_SCREW_DIST_FROM_CENTER = 41
    COVER_SCREW = data.FLAT_HEAD_SCREW_M3
    COVER_SCREW_HEAD_HEIGHT_TOLERANCE = 0.5  # should not touch the ground
    COVER_SCREW_HEAT_INSERT_LEN = 4
    COVER_SCREW_RIM = 2  # rim in all directions

    TOLERANCE = 0.1

    def __init__(self, keyboard_side: KeyboardSide):
        self._keyboard_side = keyboard_side

    @property
    def outer_radius(self) -> mm:
        return self.COVER_RADIUS + self.THICKNESS_RIM/2 + self.TOLERANCE

    def create_plate(self) -> Part:
        """ origin: z=0 => bottom of plate
        """
        body = self._create_body_with_rim()
        cover_holder_neg_parts = self._create_cover_holder_neg_parts()
        cover_holders = list(self._iter_cover_holders())
        finger_post = self._create_finger_post()
        thumb_post = self._create_thumb_post()
        trrs_socket_body = self._create_trrs_socket_body()
        trrs_socket_neg_part = self._create_trrs_socket_neg_part()
        controller_neg_part = self._create_controller_neg_part()
        controller_holder = self._create_controller_holder()
        controller_usb_hole = self._create_controller_usb_hole()
        controller_screw_hole = self._create_controller_screw_hole()
        thumb_cabel_hole = self._create_thumb_cabel_hole()
        finger_cabel_hole = self._create_finger_cabel_hole()

        part = body - cover_holder_neg_parts + cover_holders \
            + finger_post + thumb_post \
            + trrs_socket_body - trrs_socket_neg_part \
            - controller_neg_part + controller_holder - controller_usb_hole - controller_screw_hole \
            - thumb_cabel_hole - finger_cabel_hole
        part.label = 'plate'

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(part, OUTPUT_DPATH / 'circle-base-plate.stl')

        return part
    
    def _create_body_with_rim(self) -> Part:
        body = self._create_cut_circle(r=self.outer_radius, 
                                       h=self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT, 
                                       fillet_radius=self.TOP_FILLET_RADIUS)
        neg_part = self._create_cut_circle(r=self.outer_radius - self.THICKNESS_RIM, 
                                           h=self.INTERIOR_HEIGHT + self.COVER_HEIGHT, 
                                           fillet_radius=self.TOP_FILLET_RADIUS - max(self.THICKNESS_RIM, self.THICKNESS_TOP))
        controller_corner = self._create_controller_corner()
        cover_step = self._create_cover_step_for_plate()

        return body - (neg_part - controller_corner) - cover_step
    
    def _create_cut_circle(self, r: mm, h: mm, fillet_radius: mm) -> Part:
        cyl = Pos(Z=h / 2) * Cylinder(radius=r, height=h)
        top_edge = cyl.edges().sort_by(Axis.Z)[-1]
        return fillet(top_edge, fillet_radius)
    
        # a = 2 * r
        # dy = self.REL_HEIGHT * r
        # neg_box = Pos(Y=-a/2 - dy) * Box(a, a, a)
        # return cyl - neg_box
        # return cyl
    
    def _create_controller_corner(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT

        corner_x_len = self.outer_radius  # more than enough
        corner_y_len = self.outer_radius  # more than enough
        corner_height = self.INTERIOR_HEIGHT + self.COVER_HEIGHT
        corner_x = corner_x_len / 2 - (data.PICO_BOARD.width / 2 + self.TOLERANCE)
        corner_y = corner_y_len / 2 + (data.PICO_BOARD.length / 2 + self.TOLERANCE)
        corner_box = Pos(corner_x, corner_y, corner_height / 2) * Box(corner_x_len, corner_y_len, corner_height)

        return Pos(x0, y0, z0) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * corner_box
    
    def _create_cover_step_for_plate(self) -> Part:
        r = self.outer_radius - self.THICKNESS_RIM / 2
        h = self.COVER_HEIGHT
        return Pos(Z=h/2) * Cylinder(radius=r, height=h)
    
    def _create_cover_holder_neg_parts(self) -> list[Part]:
        z0 = self.COVER_HEIGHT
        h = self.INTERIOR_HEIGHT + self.THICKNESS_TOP - 2  # -2: remain top height (s. _iter_cover_holders)
        return [Pos(x, y, z0 + h/2) * Cylinder(radius=self.COVER_SCREW.head_set_insert_radius, height=h)
                for x, y in self._iter_cover_screw_positions()]
    
    def _iter_cover_screw_positions(self) -> Iterator[tuple[mm, mm]]:
        r = self.COVER_SCREW_DIST_FROM_CENTER
        n = self.COVER_NUM_SCREWS

        for i in range(n):
            angle_degree = self.COVER_SCREW_START_ANGLE + i* 360/n
            angle_radians = math.radians(angle_degree)
            x = r * math.cos(angle_radians)
            y = r * math.sin(angle_radians)
            yield x, y

    def _iter_cover_holders(self) -> Iterator[Part]:
        body_height = self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT
        screw_head_height = self.COVER_SCREW.head_height + self.COVER_SCREW_HEAD_HEIGHT_TOLERANCE  # s. create_cover
        screw_hole_radius = self.COVER_SCREW.radius + self.TOLERANCE  # s. create_cover
        z0 = screw_head_height + self.COVER_SCREW_RIM

        heat_insert_radius = self.COVER_SCREW.head_set_insert_radius
        heat_insert_len = self.COVER_SCREW_HEAT_INSERT_LEN
        holder_radius = heat_insert_radius + self.COVER_SCREW_RIM
        holder_height = body_height - z0 - 2  # -2: remain top height (s. _create_cover_holder_neg_parts)
        screw_hole_len = holder_height
        assert screw_hole_len >= heat_insert_len

        for x, y in self._iter_cover_screw_positions():
            holder_body = Pos(Z=holder_height/2) * Cylinder(radius=holder_radius, height=holder_height)
            screw_hole = Pos(Z=screw_hole_len/2) * Cylinder(radius=screw_hole_radius, height=screw_hole_len)
            heat_insert_hole = Pos(Z=heat_insert_len/2) * Cylinder(radius=heat_insert_radius, height=heat_insert_len)
            part = holder_body - screw_hole - heat_insert_hole
            yield Pos(X=x, Y=y, Z=z0) * part
    
    def _create_finger_post(self) -> Part:
        pos_radius = self.outer_radius - self.FINGER_POST_POS_DIST_FROM_BORDER
        return self._create_post(pos_angle=self.FINGER_POST_POS_ANGLE, pos_radius=pos_radius,
                                 sphere_radius=self.FINGER_POST_SPHERE_RADIUS,
                                 handle_radius=self.FINGER_POST_HANDLE_RADIUS, handle_len=self.FINGER_POST_HANDLE_LEN)

    def _create_thumb_post(self) -> Part:
        pos_radius = self.outer_radius - self.THUMB_POST_POS_DIST_FROM_BORDER
        return self._create_post(pos_angle=self.THUMB_POST_POS_ANGLE, pos_radius=pos_radius,
                                 sphere_radius=self.THUMB_POST_SPHERE_RADIUS,
                                 handle_radius=self.THUMB_POST_HANDLE_RADIUS, handle_len=self.THUMB_POST_HANDLE_LEN)

    def _create_post(self, pos_angle: Degree, pos_radius: mm, sphere_radius: mm, handle_radius: mm, handle_len: mm) -> Part:
        angle_rad = math.radians(pos_angle)
        x = pos_radius * math.cos(angle_rad)
        y = pos_radius * math.sin(angle_rad)
        z = self.THICKNESS_TOP + self.INTERIOR_HEIGHT + self.COVER_HEIGHT

        z_sphere = z + handle_len + sphere_radius

        cyl_len = handle_len + sphere_radius
        handle = Pos(x, y, z + cyl_len/2) * Cylinder(radius=handle_radius, height=cyl_len)
        sphere = Pos(x, y, z_sphere) * Sphere(radius=sphere_radius)
        return handle + sphere

    def _create_trrs_socket_body(self) -> Part:
        z0 = self.COVER_HEIGHT
        cyl_len = data.TRRS_SOCKET.cylinder_length

        body_x_len = cyl_len + data.TRRS_SOCKET.box_length + 2 * self.TRRS_SOCKET_RIM + 2 * self.TOLERANCE - self.THICKNESS_RIM
        body_y_len = data.TRRS_SOCKET.box_width + 2 * self.TOLERANCE + 2 * self.TRRS_SOCKET_RIM
        body_height = self.INTERIOR_HEIGHT
        body_x_pos = self.outer_radius - self.THICKNESS_RIM - body_x_len/2

        return Rot(Z=self.TRRS_SOCKET_POS_ANGLE) * Pos(X=body_x_pos, Z=z0 + body_height/2) * Box(body_x_len, body_y_len, body_height)

    def _create_trrs_socket_neg_part(self) -> Part:
        z0 = self.COVER_HEIGHT

        cyl_radius = data.TRRS_SOCKET.cylinder_radius + self.TOLERANCE
        cyl_len = data.TRRS_SOCKET.cylinder_length
        cyl_x_pos = self.outer_radius - cyl_len/2

        box_x_len = data.TRRS_SOCKET.box_length
        box_y_len = data.TRRS_SOCKET.box_width + 2 * self.TOLERANCE
        box_height = data.TRRS_SOCKET.box_height + self.TOLERANCE
        box_x_pos = self.outer_radius - cyl_len - box_x_len / 2

        box = Pos(X=box_x_pos, Z=z0 + box_height/2) * Box(box_x_len, box_y_len, box_height)
        cyl = Pos(X=cyl_x_pos, Z=z0 + box_height/2) * Rot(Y=90) * Cylinder(radius=cyl_radius, height=cyl_len)

        lower_cabel_box_x_len = (cyl_len + box_x_len) - self.THICKNESS_RIM
        lower_cabel_box_height = data.TRRS_SOCKET.cable_space
        lower_cabel_box_y_len = self.TRRS_SOCKET_RIM
        lower_cabel_box_x_pos = self.outer_radius - self.THICKNESS_RIM - lower_cabel_box_x_len/2
        lower_cabel_box_y_pos = box_y_len/2 + lower_cabel_box_y_len/2
        if self._keyboard_side == KeyboardSide.LEFT:
            lower_cabel_box_y_pos *= -1 
        lower_cabel_box = Pos(lower_cabel_box_x_pos, lower_cabel_box_y_pos, z0 + lower_cabel_box_height/2) * Box(lower_cabel_box_x_len, lower_cabel_box_y_len, lower_cabel_box_height)

        end_cabel_box_x_len = data.TRRS_SOCKET.cable_space
        end_cabel_box_y_len = box_y_len + self.TRRS_SOCKET_RIM
        end_cabel_box_x_pos = self.outer_radius - cyl_len - box_x_len + end_cabel_box_x_len/2
        end_cabel_box_y_pos = end_cabel_box_y_len/2
        if self._keyboard_side == KeyboardSide.LEFT:
            end_cabel_box_y_pos *= -1
        end_cabel_box = Pos(end_cabel_box_x_pos, end_cabel_box_y_pos, z0 + box_height/2) * Box(end_cabel_box_x_len, end_cabel_box_y_len, box_height)

        end_space_box_x_len = self.TRRS_SOCKET_RIM + 2 * self.TOLERANCE
        end_space_box_y_len = box_y_len + 2 * self.TRRS_SOCKET_RIM
        end_space_box_height = box_height
        ens_space_box_x_pos = self.outer_radius - cyl_len - box_x_len - end_space_box_x_len/2
        end_space_box = Pos(X=ens_space_box_x_pos, Z=z0 + end_space_box_height/2) * Box(end_space_box_x_len, end_space_box_y_len, end_space_box_height)

        return Rot(Z=self.TRRS_SOCKET_POS_ANGLE) * (cyl + box + lower_cabel_box + end_cabel_box + end_space_box)

    def _create_controller_neg_part(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT
        ctrl_height = data.PICO_BOARD.get_total_height_with_feet()

        body_len = data.PICO_BOARD.length + 2 * self.TOLERANCE  # + data.PICO_BOARD.usb_len_over_board
        body_width = data.PICO_BOARD.width + 2 * self.TOLERANCE
        body_height = ctrl_height + 2 * self.TOLERANCE
        body = Box(body_width, body_len, body_height)

        return Pos(x0, y0, z0 + body_height/2) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * body

    def _create_controller_holder(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT
        rim = self.CONTROLLER_RIM
        inner_len = data.PICO_BOARD.length + 2 * self.TOLERANCE  # + data.PICO_BOARD.usb_len_over_board
        inner_width = data.PICO_BOARD.width + 2 * self.TOLERANCE
        ctrl_height = data.PICO_BOARD.get_total_height_with_feet()
        inner_height = ctrl_height + 2 * self.TOLERANCE

        board_rim_pos_len = inner_len + 2 * rim
        board_rim_pos_width = inner_width + 2 * rim
        board_rim_height = data.PICO_BOARD.usb_height + data.PICO_BOARD.height + self.TOLERANCE
        board_rim_z = inner_height - board_rim_height/2
        board_rim_pos = Pos(Z=board_rim_z) * Box(board_rim_pos_width, board_rim_pos_len, board_rim_height)
        board_rim_neg = Pos(Z=board_rim_z) * Box(inner_width, inner_len, board_rim_height)

        screw_base_radius = self.CONTROLLER_HOLD_SCREW.head_set_insert_radius + rim
        screw_base_dy = data.PICO_BOARD.length/2 + self.CONTROLLER_HOLD_SCREW_DIST_FROM_BOARD
        screw_base = Pos(Y=-screw_base_dy, Z=board_rim_z) * Cylinder(radius=screw_base_radius, height=board_rim_height)

        dist_holder_len = max(data.PICO_BOARD.pins_height, data.PICO_BOARD.usb_height) + self.TOLERANCE
        dist_holders = list(self._iter_controller_dist_holder())
        
        top_holder_x_len = data.PICO_BOARD.usb_width + 2 * 1  # a little bit wider, than the usb port
        top_holder_y_len = 3
        top_holder_height = 2
        top_holder_y = inner_len / 2 - top_holder_y_len / 2
        top_holder_z = inner_height - dist_holder_len - data.PICO_BOARD.height - top_holder_height/2 - 10 * self.TOLERANCE
        top_holder = Pos(Y=top_holder_y, Z=top_holder_z) * Box(top_holder_x_len, top_holder_y_len, top_holder_height)
        
        part = board_rim_pos - board_rim_neg + top_holder + dist_holders + screw_base
        return Pos(x0, y0, z0) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * part
    
    def _iter_controller_dist_holder(self) -> Iterator[Part]:
        ctrl_height = data.PICO_BOARD.get_total_height_with_feet()
        inner_height = ctrl_height + 2 * self.TOLERANCE

        x_small_len = 3
        y_len = 4
        box_height = max(data.PICO_BOARD.pins_height, data.PICO_BOARD.usb_height) + self.TOLERANCE

        dx = data.PICO_BOARD.usb_width/2 + self.TOLERANCE + x_small_len/2
        dy = data.PICO_BOARD.length/2 + self.TOLERANCE - y_len/2
        z = inner_height - box_height/2

        small_box = Box(x_small_len, y_len, box_height)
        yield Pos(-dx, dy, z) * small_box
        yield Pos(dx, dy, z) * small_box

        x_big_len = x_small_len + 2 * dx
        big_box = Box(x_big_len, y_len, box_height)
        yield Pos(0, -dy, z) * big_box

    def _create_controller_usb_hole(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT

        usb_box_width = self.CONTROLLER_USB_HOLE_WIDTH
        usb_box_z = data.PICO_BOARD.pcb_terminal_height + data.PICO_BOARD.height + data.PICO_BOARD.usb_height / 2
        usb_box_height = self.CONTROLLER_USB_HOLE_HEIGHT

        if self._keyboard_side == KeyboardSide.RIGHT:
            usb_box_deep = self.CONTROLLER_RIM
            inner_height = data.PICO_BOARD.get_total_height_with_feet() + 2 * self.TOLERANCE
            if usb_box_z + usb_box_height/2 > inner_height:
                dz = usb_box_z + usb_box_height/2 - inner_height
                usb_box_height -= dz
                usb_box_z -= dz/2
        else:
            usb_box_deep = self.outer_radius

        body_len = data.PICO_BOARD.length + 2 * self.TOLERANCE
        usb_box_y = body_len/2 + usb_box_deep/2

        usb_box = Pos(Y=usb_box_y, Z=usb_box_z) * Box(usb_box_width, usb_box_deep, usb_box_height)
        return Pos(x0, y0, z0) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * usb_box
    
    def _create_controller_screw_hole(self) -> Part:
        angle_radians = math.radians(self.CONTROLLER_POS_ANGLE)
        pos_radius = self.CONTROLLER_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT + data.PICO_BOARD.pcb_terminal_height + 2 * self.TOLERANCE

        screw = self.CONTROLLER_HOLD_SCREW
        dy = data.PICO_BOARD.length/2 + self.CONTROLLER_HOLD_SCREW_DIST_FROM_BOARD
        h = self.CONTROLLER_HOLD_SCREW_HOLE_LEN

        cyl = Pos(Y=-dy, Z=h/2) * Cylinder(radius=screw.head_set_insert_radius, height=h)
        return Pos(x0, y0, z0) * Rot(Z=self.CONTROLLER_ROT_ANGLE) * cyl
    
    def _iter_controller_dist_holder_positions(self) -> Iterator[tuple[mm, mm]]:
        y_len = data.PICO_BOARD.length
        x_len = data.PICO_BOARD.width
        y1 = data.PICO_BOARD.hole_distance_top
        y2 = data.PICO_BOARD.hole_distance_bottom
        x1 = data.PICO_BOARD.hole_distance_left
        x2 = data.PICO_BOARD.hole_distance_right

        yield -x_len/2 + x1, y_len/2 - y1
        yield  x_len/2 - x2, y_len/2 - y1
        yield -x_len/2 + x1, -y_len/2 + y2
        yield  x_len/2 - x2, -y_len/2 + y2
    
    def _create_thumb_cabel_hole(self) -> Part:
        angle_radians = math.radians(self.THUMB_CABEL_HOLE_POS_ANGLE)
        pos_radius = self.THUMB_CABEL_HOLE_POS_DIST_FROM_CENTER
        x0 = pos_radius * math.cos(angle_radians)
        y0 = pos_radius * math.sin(angle_radians)
        z0 = self.COVER_HEIGHT + self.INTERIOR_HEIGHT
        height = self.THICKNESS_TOP
        return Pos(x0, y0, z0 + height/2) * Cylinder(radius=self.THUMB_CABEL_HOLE_RADIUS, height=height)
    
    def _create_finger_cabel_hole(self) -> Part:
        # cabel_radius = self.INTERIOR_HEIGHT / 2
        # height = 10
        # z = self.COVER_HEIGHT + self.INTERIOR_HEIGHT / 2
        # return Rot(Z=self.FINGER_CABEL_HOLE_POS_ANGLE) * Pos(X=self.outer_radius, Z=z) * Rot(Y=90) * Cylinder(radius=cabel_radius, height=height)

        hole_heigh = self.COVER_HEIGHT + self.FINGER_CABEL_HOLE_HEIGHT
        hole_x_len = 40  # exact value does not matter
        hole_y_len = self.FINGER_CABEL_HOLE_WIDTH
        z = hole_heigh / 2
        return Rot(Z=self.FINGER_CABEL_HOLE_POS_ANGLE) * Pos(X=self.outer_radius, Z=z) * Rot(Z=self.FINGER_CABEL_ROT) * Box(hole_x_len, hole_y_len, hole_heigh)

    def create_cover(self) -> Part:
        slice_radius = self.COVER_RADIUS
        slice_height = self.COVER_HEIGHT
        slice = Pos(Z=slice_height/2) * Cylinder(radius=slice_radius, height=slice_height)

        screw_head_height = self.COVER_SCREW.head_height + self.COVER_SCREW_HEAD_HEIGHT_TOLERANCE
        screw_head_radius = self.COVER_SCREW.head_radius + self.TOLERANCE
        screw_head_neg_cyl = Pos(Z=screw_head_height/2) * Cylinder(radius=screw_head_radius, height=screw_head_height)

        screw_hole_radius = self.COVER_SCREW.radius + self.TOLERANCE
        screw_hole_len = 100
        screw_hole = Pos(Z=screw_hole_len/2) * Cylinder(radius=screw_hole_radius, height=screw_hole_len)

        screw_post_radius = screw_head_radius + self.COVER_SCREW_RIM
        screw_post_height = screw_head_height + self.COVER_SCREW_RIM - slice_height
        screw_post_body = Pos(Z=slice_height + screw_post_height/2) * Cylinder(radius=screw_post_radius, height=screw_post_height)

        screw_posts_pos = [Pos(X=x, Y=y) * screw_post_body
                           for x, y in self._iter_cover_screw_positions()]
        screw_posts_neg = [Pos(X=x, Y=y) * (screw_head_neg_cyl + screw_hole)
                           for x, y in self._iter_cover_screw_positions()]

        part = slice + screw_posts_pos - screw_posts_neg
        part.label = 'cover'

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()
            
            export_stl(part, OUTPUT_DPATH / 'circle-base-cover.stl')
        
        return part

    def create_trrs_stopper(self) -> Solid: 
        overlap = 2
        height = data.TRRS_SOCKET.box_height
        length = data.TRRS_SOCKET.box_width + 2 * self.TRRS_SOCKET_RIM + 2 * overlap
        width = self.TRRS_SOCKET_RIM

        box = Box(length, width, height)

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(box, OUTPUT_DPATH / 'trrs_stopper.stl')

        return box

    def create_controller_holder(self) -> Solid:
        height = 2
        width = 8
        length = 18
        box = Box(length, width, height)
        screw = data.FLAT_HEAD_SCREW_M2
        r = screw.hole_radius + self.TOLERANCE
        hole = Pos(X=length/2 - 5) * Cylinder(radius=r, height=height)
        part = box - hole

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(part, OUTPUT_DPATH / 'controller-holder-plate.stl')

        return part
    
        

    

if __name__ == '__main__':
    main()
