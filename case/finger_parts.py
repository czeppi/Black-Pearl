import copy
import math
from pathlib import Path
from typing import Iterator
from dataclasses import dataclass

from base import OUTPUT_DPATH
from hot_swap_socket import HotSwapSocketCreator3, hot_swap_socket_data, kailh_choc_v1_data
from finger_parts_common import LEFT_RIGHT_BORDER, CUT_WIDTH, SwitchPairHolderFingerLocations
from double_ball_join import FingerDoubleBallJoinCreator
import data

from build123d import Box, Circle, Compound, CounterBoreHole, Hole, Cylinder, Edge, Part, Plane, Polyline, Pos, Rot, Location, Sketch, Solid, Sphere, Vector, export_stl, extrude, make_face, sweep
from ocp_vscode import show


type XY = tuple[float, float]

WRITE_ENABLED = True  # set this to False, if you only want to see the results


@dataclass
class SwitchHolderCorrection:
    dx: float = 0.0
    dy: float = 0.0
    dz: float = 0.0


#class SwitchHolderCorrections:
    #single_switch: SwitchHolderCorrection = field(default_factory=SwitchHolderCorrection)
    #index: PosCorrection
    #middle: PosCorrection
    #ring: PosCorrection
    #pinkie: PosCorrection


class CaseAssemblyCreator:

    def __init__(self):
        self._skeleton: Part | None = None
        self._holders: list[Solid] = None

    def create(self) -> Compound:
        self._skeleton = SkeletonCreator().create()
        children = [self._skeleton] + list(self._iter_switch_holders())
        return Compound(label="case_assembly", children=children)

    def _iter_switch_holders(self) -> Iterator[Compound]:
        loc = SwitchPairHolderFingerLocations()

        # y2 = 11.36  # SwitchPairHolderCreator._create_middle_profile_face()#y2
        # holder = Box(14, 2 * y2, 5)

        pair_holder_parts = SwitchPairHolderCreator().create()
        index2_compound = SingleSwitchHolderCreator().create()

        yield loc.index * index2_compound
        yield loc.index * Compound(label='index', children=copy.copy(pair_holder_parts))
        yield loc.middle * Compound(label='middle', children=copy.copy(pair_holder_parts))
        yield loc.ring * Compound(label='ring', children=copy.copy(pair_holder_parts))
        yield loc.pinkie * Compound(label='pinkie', children=copy.copy(pair_holder_parts))

    def save(self, output_path: Path) -> None:
        raise NotImplementedError()


class SwitchHolderCreatorBase:
    TOLERANCE = 0.1
    MIDDLE_PART_HEIGHT_AT_CENTER = 3.0
    CABLE_DIAMETER = 1.3  # AWG26 without tolerance
    CABLE_SLOT_Y = 7.0

    @property
    def _square_hole_len(self) -> float:
        return kailh_choc_v1_data.SUB_BODY_SIZE + 2 * self.TOLERANCE

    @property
    def _square_hole_height(self) -> float:
        return kailh_choc_v1_data.SUB_BODY_HEIGHT - self.TOLERANCE

    def _iter_switch_holes(self) -> Iterator[Solid]:
        data = kailh_choc_v1_data
        tol = self.TOLERANCE
        height = data.STUBS_HEIGHT + tol
        z_off = hot_swap_socket_data.STUDS_HEIGHT - height/2
        yield Pos(Z=z_off) * Cylinder(radius=data.CENTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=z_off, X=-data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)
        yield Pos(Z=z_off, X=data.OUTER_STUB_CX) * Cylinder(radius=data.OUTER_STUB_RADIUS + tol, height=height)

    @staticmethod
    def _iter_hot_swap_socket_studs() -> Iterator[Solid]:
        data = hot_swap_socket_data
        h = data.STUDS_HEIGHT
        r = data.STUDS_RADIUS
        cyl = Pos(Z=h/2) * Cylinder(radius=r, height=h)
        dx = data.STUDS_DX / 2
        dy = data.STUDS_DY / 2

        y0 = hot_swap_socket_data.Y_OFFSET
        x0 = hot_swap_socket_data.X_OFFSET

        yield Pos(X=x0 - dx, Y=y0 + dy) * copy.copy(cyl)
        yield Pos(X=x0 + dx, Y=y0 - dy) * copy.copy(cyl)

    @staticmethod
    def _create_counter_bore_hole(screw: data.FlatHeadScrew, extra_depth: float = 0.0) -> Part:
        return CounterBoreHole(radius=screw.hole_radius,
                               counter_bore_radius=screw.head_radius,
                               counter_bore_depth=screw.head_height + extra_depth,
                               depth=100)
    
    def _create_hole(self, screw: data.FlatHeadScrew) -> Part:
        return Hole(radius=screw.hole_radius, depth=100)

    @staticmethod
    def create_heat_set_insert_hole(screw: data.FlatHeadScrew, extra_depth: float = 0.0) -> Part:
        counter_bore_depth = 2.0 + extra_depth

        return CounterBoreHole(radius=screw.hole_radius,
                               counter_bore_radius=screw.head_set_insert_radius,
                               counter_bore_depth=counter_bore_depth,
                               depth=counter_bore_depth + 2)  # not to deep, cause of skeleton tube


class SingleSwitchHolderCreator(SwitchHolderCreatorBase):  # for index finger
    HOLDER_LEFT_RIGHT_BORDER = 6.0  # for screws
    HOLDER_FRONT_BACK_BORDER = 1.0
    TILT_ANGLE = 25
    FOOT_RIGHT_HEIGHT = 4  # on the right side (smallest height)
    X_OFFSET = -20  # from index location
    CORRECTIONS = SwitchHolderCorrection(dz=3, dx=-3)

    def _iter_top_foot_conn_points(self) -> Iterator[XY]:
        """ before Rot(Z=90)
        """
        hole_len = self._square_hole_len
        x = hole_len / 2 + self.HOLDER_LEFT_RIGHT_BORDER / 2
        yield -x, 0
        yield x, 0

    def iter_foot_base_conn_points(self) -> Iterator[XY]:
        """ after Rot(Z=90)
        """
        yield 0, 0

    def create(self) -> Compound:
        """ - create top + middle part with top faces parallel to xy plane
            - rotate than: Rot(Z=90) + Rot(Y)
            - create foot with bottom face parallel to xy plane
        """
        top_part1 = self._create_top()
        middle_part1 = self._create_middle_part()
        
        dz = self.MIDDLE_PART_HEIGHT_AT_CENTER
        loc1 = Rot(Y=self.TILT_ANGLE) * Pos(Z=dz) * Rot(Z=90)
        #  after          after          after                        
        #  Rot(Z=90)      Pos(Z=dz1)     Rot(Y=...)
        #                     z               z    
        #      z          T T | T T        T  |         
        #  T T | T T      M M | M M        M  |  T       
        #  ----o----> x   ----o----> x   -----o------> x
        #  M M | M M          |               |  M
        #
        # T = top part,  M = middle part

        top_part2 = loc1 * top_part1
        middle_part2 = loc1 * middle_part1
        foot_part = self._create_foot()

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(top_part2, OUTPUT_DPATH / 'single-switch-top.stl')
            export_stl(middle_part2, OUTPUT_DPATH / 'single-switch-middle.stl')
            export_stl(foot_part, OUTPUT_DPATH / 'single-switch-foot.stl')

        r = self._square_hole_len / 2 + self.HOLDER_FRONT_BACK_BORDER
        angle_rad = math.radians(self.TILT_ANGLE)
        z_offset = r * math.sin(angle_rad) - self.MIDDLE_PART_HEIGHT_AT_CENTER

        parts = [top_part2, middle_part2, foot_part]
        dx = self.X_OFFSET + self.CORRECTIONS.dx
        dz = z_offset + self.CORRECTIONS.dz
        return Pos(X=dx, Z=dz) * Compound(label='index2', children=parts)

    def _create_top(self) -> Solid:
        """ 
        origin: x, y: center of hole, z: bottom of top part
        """
        x_border = self.HOLDER_LEFT_RIGHT_BORDER
        y_border = self.HOLDER_FRONT_BACK_BORDER

        hole_len = self._square_hole_len
        hole_height = self._square_hole_height
        studs_height = hot_swap_socket_data.STUDS_HEIGHT

        box_dx = hole_len + 2 * x_border
        box_dy = hole_len + 2 * y_border
        box_dz = hole_height + studs_height

        body = Pos(Z=box_dz/2) * Box(box_dx, box_dy, box_dz)
        square_hole = Pos(Z=hole_height/2 + studs_height) * Box(hole_len, hole_len, hole_height)

        switch_holes = list(self._iter_switch_holes())
        hot_swap_socket_studs = list(self._iter_hot_swap_socket_studs())
        counter_bore_holes = list(self._create_top_counter_bore_holes())
        neg_parts = [square_hole] + switch_holes + hot_swap_socket_studs + counter_bore_holes

        top_part = body - neg_parts
        top_part.label = 'top'
        return top_part

    def _create_top_counter_bore_holes(self) -> Iterator[Part]:
        h = hot_swap_socket_data.STUDS_HEIGHT + self._square_hole_height

        for x, y in self._iter_top_foot_conn_points():
            pos = Pos(X=x, Y=y, Z=h)
            hole = self._create_counter_bore_hole(screw=data.FLAT_HEAD_SCREW_M2_5)
            yield Plane.XY * pos * hole

    def _create_middle_part(self) -> Solid:
        x_border = self.HOLDER_LEFT_RIGHT_BORDER
        y_border = self.HOLDER_FRONT_BACK_BORDER

        hole_len = self._square_hole_len
        box_dx = hole_len + 2 * x_border
        box_dy = hole_len + 2 * y_border
        box_dz = self.MIDDLE_PART_HEIGHT_AT_CENTER
        body = Pos(Z=-box_dz/2) * Box(box_dx, box_dy, box_dz)

        x_off = hot_swap_socket_data.X_OFFSET
        y_off = hot_swap_socket_data.Y_OFFSET
        z_off = hot_swap_socket_data.STUDS_HEIGHT
        hot_swap_socket = Pos(X=x_off, Y=y_off, Z=z_off) * HotSwapSocketCreator3().create()

        switch_holes = [hole for hole in self._iter_switch_holes()]
        screw_holes = list(self._iter_middle_screw_holes())
        neg_parts = [hot_swap_socket] + screw_holes + switch_holes

        middle_part = body - neg_parts
        middle_part.label = 'middle'
        return middle_part

    def _iter_middle_screw_holes(self) -> Iterator[Solid]:
        for x, y in self._iter_top_foot_conn_points():
            pos = Pos(X=x, Y=y)
            hole = self._create_hole(screw=data.FLAT_HEAD_SCREW_M2_5)
            yield Plane.XY * pos * hole

    def _create_foot(self) -> Solid:
        body = self._create_foot_body()
        heat_set_insert_holes = list(self._iter_foot_heat_set_insert_holes())
        counter_bore_holes = list(self._iter_foot_counter_bore_holes())

        foot_part = body - heat_set_insert_holes - counter_bore_holes
        foot_part.label = 'foot'
        return foot_part

    def _create_foot_body(self) -> Solid:
        face = self._create_foot_profile_face()
        deep = self._square_hole_len + 2 * self.HOLDER_LEFT_RIGHT_BORDER

        return Pos(Y=deep/2) * extrude(face, deep)

    def _create_foot_profile_face(self) -> Sketch:
        points = list(self._iter_foot_profile_points())

        return make_face(Plane.XZ * Polyline(points))
    
    def _iter_foot_profile_points(self) -> Iterator[tuple[float, float]]:
        """
        order of points:
               z
           1   |    
           ----+-------> x
               |   0
           2   |   3
        """
        r = self._square_hole_len / 2 + self.HOLDER_FRONT_BACK_BORDER
        angle_rad = math.radians(self.TILT_ANGLE)

        x03 = r * math.cos(angle_rad)
        x12 = -x03
        z1 = r * math.sin(angle_rad)
        z0 = -z1
        z23 = z0 - (self.FOOT_RIGHT_HEIGHT + self.CORRECTIONS.dz)

        yield x03, z0
        yield x12, z1
        yield x12, z23
        yield x03, z23
        yield x03, z0

    def _iter_foot_heat_set_insert_holes(self) -> Iterator[Solid]:
        """ top face is parallel in xy plane (but already Rot(Z=90))
        """
        for x, y in self._iter_top_foot_conn_points():
            pos = Rot(Y=self.TILT_ANGLE) * Rot(Z=90) * Pos(X=x, Y=y)
            hole = self.create_heat_set_insert_hole(screw=data.FLAT_HEAD_SCREW_M2_5)
            yield  Plane.XY * pos * hole

    def _iter_foot_counter_bore_holes(self) -> Iterator[Part]:
        """ top face is rotated (and Rot(Z=90))
        """
        screw = data.FLAT_HEAD_SCREW_M2
        angle_rad = math.radians(self.TILT_ANGLE)
        extra_depth = screw.head_radius * math.tan(angle_rad)

        screw_len = 6
        screw_hole_len = screw_len - 3  # hole must be shorter than screw!

        bore_z = 10  # any value big enough
        z_min = min(z for _, z in self._iter_foot_profile_points())
        counter_bore_depth = (bore_z - z_min)- screw_hole_len

        for x0, y0 in self.iter_foot_base_conn_points():
            x = x0 - self.CORRECTIONS.dx
            y = y0 - self.CORRECTIONS.dy
            pos = Pos(X=x, Y=y, Z=bore_z)
            hole = CounterBoreHole(radius=screw.hole_radius,
                                   counter_bore_radius=screw.head_radius,
                                   counter_bore_depth=counter_bore_depth,
                                   depth=100)
            yield Plane.XY * pos * hole


class SwitchPairHolderCreator(SwitchHolderCreatorBase):
    TILT_ANGLE = 15  # 15 degree for each side
    HOLDER_LEFT_RIGHT_BORDER = 1.0
    HOLDER_FRONT_BORDER = 3.2  # s. finger_parts.py#BACK_BORDER
    HOLDER_BACK_BORDER = 1.0
    FOOT_HEIGHT = 4
    FOOT_Y_LEN = 22.7

    def _iter_top_foot_conn_points(self) -> Iterator[XY]:
        yield 0, 0

    def iter_foot_base_conn_points(self) -> Iterator[XY]:
        dy = 5
        yield 0, dy
        yield 0, -dy

    def create(self) -> list[Solid]:
        top_part = self._create_top()
        middle_part = self._create_middle_part()
        foot_part = self._create_foot()

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(top_part, OUTPUT_DPATH / 'switch-pair-top.stl')
            export_stl(middle_part, OUTPUT_DPATH / 'switch-pair-middle.stl')
            export_stl(foot_part, OUTPUT_DPATH / 'switch-pair-foot.stl')

        return [top_part, middle_part, foot_part]

    def _create_top(self) -> Solid:
        back_part = self._create_top_back_part()
        back_box = back_part.bounding_box()

        back_part = Rot(X=self.TILT_ANGLE) * Pos(Y=-back_box.min.Y) * back_part
        front_part = Rot(Z=180) * copy.copy(back_part)
        top_part = back_part + front_part

        # => origin: x, y: center, z: bottom of top part

        top_part -= list(self._iter_top_counter_bore_holes())

        top_part.label = 'top'
        return top_part

    def _create_top_back_part(self) -> Solid:
        """ 
        origin: x, y: center of hole, z: bottom
        """
        # 
        body = self._create_top_body()

        a = self._square_hole_len
        h = self._square_hole_height
        square_hole = Pos(Z=h/2 + hot_swap_socket_data.STUDS_HEIGHT) * Box(a, a, h)

        holes = list(self._iter_switch_holes())
        hot_swap_socket_studs = list(self._iter_hot_swap_socket_studs())

        neg_parts = [square_hole] + holes + hot_swap_socket_studs
        return body - neg_parts

    def _create_top_body(self) -> Solid:
        face = self._create_top_profile_face()
        width = 2 * self.HOLDER_LEFT_RIGHT_BORDER + self._square_hole_len

        return Pos(X=-width/2) * extrude(face, width)

    def _create_top_profile_face(self) -> Sketch:
        """
        order of points:
               z
           2   |    1
          3    +----0-----> y
        """
        angle_rad = math.radians(self.TILT_ANGLE)

        square_hole_len = self._square_hole_len
        square_hole_height = self._square_hole_height

        y01 = square_hole_len/2 + self.HOLDER_BACK_BORDER
        y2 = -square_hole_len/2 - self.HOLDER_FRONT_BORDER
        z12 = square_hole_height + hot_swap_socket_data.STUDS_HEIGHT
        y3 = y2 - z12 * math.tan(angle_rad)

        points = [
            (y01, 0),
            (y01, z12),
            (y2, z12),
            (y3, 0),
            (y01, 0),
        ]
        back_half = Polyline(points)
        return make_face(Plane.YZ * back_half)

    def _iter_top_counter_bore_holes(self) -> Iterator[Part]:
        screw = data.FLAT_HEAD_SCREW_M2_5

        angle_rad = math.radians(self.TILT_ANGLE)
        h = (hot_swap_socket_data.STUDS_HEIGHT + self._square_hole_height) /  math.cos(angle_rad)
        h_offset =  math.tan(angle_rad) * screw.head_radius

        for x, y in self._iter_top_foot_conn_points():
            pos = Pos(X=x, Y=y, Z=h+h_offset)
            hole = self._create_counter_bore_hole(screw=screw, extra_depth=h_offset)
            yield Plane.XY * pos * hole

    def _create_middle_part(self) -> Solid:
        back_part = self._create_middle_back_part()
        front_part = Rot(Z=180) * copy.copy(back_part)
        middle_part = back_part + front_part
        middle_part -= list(self._iter_middle_screw_holes())

        middle_part.label = 'middle'
        return middle_part

    def _create_middle_back_part(self) -> Solid:
        body = self._create_middle_body()
        body_box = body.bounding_box()

        angle_rad = math.radians(self.TILT_ANGLE)
        top_height = self._square_hole_height + hot_swap_socket_data.STUDS_HEIGHT
        y_off0 = self._square_hole_len/2 + self.HOLDER_FRONT_BORDER + top_height * math.tan(angle_rad)

        z_off = hot_swap_socket_data.STUDS_HEIGHT
        rel_socket_loc = self._create_hot_swap_socket_location_rel_to_switch_center()
        hot_swap_socket = Rot(X=self.TILT_ANGLE) * Pos(Y=y_off0, Z=z_off) * rel_socket_loc * HotSwapSocketCreator3().create()
        #hot_swap_socket_box = hot_swap_socket.bounding_box()

        holes = [Rot(X=self.TILT_ANGLE) * Pos(Y=y_off0) * hole
                 for hole in self._iter_switch_holes()]

        cable_diam = self.CABLE_DIAMETER + self.TOLERANCE
        z_off = cable_diam/2 + body_box.min.Z
        cabel_slot = Pos(Y=self.CABLE_SLOT_Y, Z=z_off) * Box(1000, cable_diam, cable_diam)

        neg_parts = [hot_swap_socket, cabel_slot] + holes
        return body - neg_parts
    
    def _create_hot_swap_socket_location_rel_to_switch_center(self) -> Location:
        x_off = hot_swap_socket_data.X_OFFSET
        y_off = hot_swap_socket_data.Y_OFFSET
        return Pos(X=x_off, Y=y_off)

    def _create_middle_body(self) -> Solid:
        face = self._create_middle_profile_face()
        width = 2 * self.HOLDER_LEFT_RIGHT_BORDER + self._square_hole_len

        return Pos(X=width/2) * extrude(face, width)

    def _create_middle_profile_face(self) -> Sketch:
        """
        order of points:
               z
               |     1
               0---------> y
               3   2
        """
        angle_rad = math.radians(self.TILT_ANGLE)

        r = self.HOLDER_FRONT_BORDER + self._square_hole_len/2 + kailh_choc_v1_data.CENTER_STUB_RADIUS + 4.0  # 4.0: to have enough margin behind the center stub
        y1 = r * math.cos(angle_rad)
        z1 = r * math.sin(angle_rad)
        y2 = self.FOOT_Y_LEN / 2 # y1 - 4.0
        z23 = -self.MIDDLE_PART_HEIGHT_AT_CENTER

        points = [
            (0, 0),
            (y1, z1),
            (y2, z23),
            (0, z23),
            (0, 0),
        ]
        back_half = Polyline(points)
        return make_face(Plane.YZ * back_half)

    def _iter_middle_screw_holes(self) -> Iterator[Solid]:
        screw = data.FLAT_HEAD_SCREW_M2_5
        angle_rad = math.radians(self.TILT_ANGLE)
        h_offset =  math.tan(angle_rad) * screw.head_set_insert_radius

        for x, y in self._iter_top_foot_conn_points():
            pos = Pos(X=x, Y=y, Z=h_offset)
            hole = self._create_hole(screw=screw)
            yield Plane.XY * pos * hole

    def _create_foot(self) -> Solid:
        x_len = 2 * self.HOLDER_LEFT_RIGHT_BORDER + self._square_hole_len
        z_offset = self.FOOT_HEIGHT / 2 + self.MIDDLE_PART_HEIGHT_AT_CENTER
        foot_part = Pos(Z=-z_offset) * Box(x_len, self.FOOT_Y_LEN, self.FOOT_HEIGHT)

        counter_bore_holes = list(self._iter_foot_counter_bore_holes())
        heat_set_insert_holes = list(self._iter_foot_heat_set_insert_holes())
        foot_part -= counter_bore_holes + heat_set_insert_holes

        foot_part.label = 'foot'
        return foot_part

    def _iter_foot_heat_set_insert_holes(self) -> Iterator[Solid]:
        for x, y in self._iter_top_foot_conn_points():
            pos = Pos(X=x, Y=y, Z=-self.MIDDLE_PART_HEIGHT_AT_CENTER)
            hole = self.create_heat_set_insert_hole(screw=data.FLAT_HEAD_SCREW_M2_5)
            yield Plane.XY * pos * hole

    def _iter_foot_counter_bore_holes(self) -> Iterator[Part]:
        for x, y in self.iter_foot_base_conn_points():
            pos = Pos(X=x, Y=y, Z=-self.MIDDLE_PART_HEIGHT_AT_CENTER)
            hole = self._create_counter_bore_hole(screw=data.FLAT_HEAD_SCREW_M2)
            yield Plane.XY * pos * hole


class SkeletonCreator:
    TUBE_OUTER_RADIUS = 10
    TUBE_INNER_RADIUS = 7
    BASE_LEN = 18
    BASE_HEIGHT = 3
    BASE_Z_OFFSET = 0.5  # make base position a little bit above the tube
    CABLE_HOLE_RADIUS = 3
    SPHERE_RADIUS = FingerDoubleBallJoinCreator.SPHERE_RADIUS
    SPHERE_HANDLE_RADIUS = FingerDoubleBallJoinCreator.HANDLE_RADIUS

    def __init__(self):
        self._dz = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER \
                   + SwitchPairHolderCreator.FOOT_HEIGHT \
                   + self.BASE_Z_OFFSET + self.TUBE_OUTER_RADIUS

    def create(self) -> Part:
        spline_edge = self._create_spline_edge()
        outer_tube = self._create_tube(r=self.TUBE_OUTER_RADIUS, spline_edge=spline_edge)
        inner_tube = self._create_tube(r=self.TUBE_INNER_RADIUS, spline_edge=spline_edge)

        switch_bases = list(self._iter_switch_bases())
        sphere = self._create_sphere()
        sphere_handle = self._create_sphere_handle()
        cable_holes = list(self._iter_cable_holes())
        heat_set_insert_holes = list(self._iter_heat_set_insert_holes())
        neg_parts = [inner_tube] + cable_holes + heat_set_insert_holes

        skeleton_with_sphere = (outer_tube + switch_bases + sphere_handle + sphere) - neg_parts
        skeleton_with_sphere.label = 'skeleton'

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(skeleton_with_sphere, OUTPUT_DPATH / 'skeleton-with-sphere.stl')

        return skeleton_with_sphere
    
    def _iter_cable_holes(self) -> Iterator[Part]:
        loc = SwitchPairHolderFingerLocations()

        hole_radius = self.CABLE_HOLE_RADIUS
        hole_height = self._dz
        base_len = self.BASE_LEN
        x_offset = base_len / 2 + hole_radius
        z_offset = hole_height / 2

        yield loc.index * Pos(X=-x_offset + 2, Z=-z_offset) * Cylinder(radius=hole_radius, height=hole_height)
        yield loc.index * Pos(X=x_offset - 1, Y=3, Z=-z_offset) * Cylinder(radius=hole_radius, height=hole_height)
        yield loc.middle * Pos(X=x_offset, Y=-1, Z=-z_offset) * Cylinder(radius=hole_radius, height=hole_height)
        yield loc.ring * Pos(X=x_offset, Y=-5, Z=-z_offset) * Cylinder(radius=hole_radius, height=hole_height)
        #yield loc.pinkie * Pos(X=x_offset, Y=-1, Z=-z_offset) * Cylinder(radius=hole_radius, height=hole_height)

    def _create_spline_edge(self) -> Edge:
        loc = SwitchPairHolderFingerLocations()
        dz = self._dz
        holder_dx = LEFT_RIGHT_BORDER + CUT_WIDTH + LEFT_RIGHT_BORDER
        skeleton_start = loc.index * Pos(X=-3/2*holder_dx, Y=-5)
        skeleton_end = loc.pinkie * Pos(X=holder_dx/2+5, Y=-5)

        points = [#Vector(-30, -15, -dz), 
                  (skeleton_start * Pos(Z=-dz)).position,
                  (loc.index * Pos(X=-holder_dx/2, Z=-dz)).position,
                  (loc.middle * Pos(Z=-dz)).position,
                  (loc.ring * Pos(Z=-dz)).position,
                  (loc.pinkie * Pos(Z=-dz)).position,
                  (skeleton_end * Pos(Z=-dz)).position]

        return Edge.make_spline_approx(points=points, tol=0.01, max_deg=3)

    def _create_tube(self, r: float, spline_edge: Edge) -> Part:
        profile_template = Circle(1.0 * r)  # Circle(0.9 * r)
        profile_template2 = Circle(1.0 * r)  # Circle(1.1 * r)

        start_tangent = spline_edge%0
        x_dir = start_tangent.cross(Vector(0, 0, 1)).normalized()
        plane0 = Plane(origin=spline_edge@0, z_dir=start_tangent, x_dir=x_dir)
        profile0 = plane0 * profile_template

        end_tangent = spline_edge%1
        x_dir = end_tangent.cross(Vector(0, 0, 1)).normalized()
        plane1 = Plane(origin=spline_edge@1, z_dir=end_tangent, x_dir=x_dir)
        profile1 = plane1 * profile_template2

        return sweep([profile0, profile1], path=spline_edge, multisection=True)

    def _iter_switch_bases(self) -> Iterator[Part]:
        loc = SwitchPairHolderFingerLocations()

        base_height = self.BASE_HEIGHT
        base_len = self.BASE_LEN
        index_base_width = 2 * base_len + 1
        z_dist = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER \
                 + SwitchPairHolderCreator.FOOT_HEIGHT \
                 + base_height / 2
        
        switch_pair_holder = SwitchPairHolderCreator()
        pair_holder_heat_set_insert_holes = [
            Pos(X=x, Y=y, Z=base_height/2) * SwitchHolderCreatorBase._create_counter_bore_hole(screw=data.FLAT_HEAD_SCREW_M2)
            for x, y in switch_pair_holder.iter_foot_base_conn_points()]

        big_box = Box(index_base_width, base_len, base_height)
        small_box = Box(base_len, base_len, base_height) - pair_holder_heat_set_insert_holes

        yield loc.index * Pos(X=(base_len - index_base_width) / 2, Z=-z_dist) * big_box
        yield loc.middle * Pos(Z=-z_dist) * copy.copy(small_box)
        yield loc.ring * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)
        yield loc.pinkie * Pos(Z=-z_dist) * Box(base_len, base_len, base_height)

    def _iter_heat_set_insert_holes(self):
        loc = SwitchPairHolderFingerLocations()
        z_dist = SwitchPairHolderCreator.MIDDLE_PART_HEIGHT_AT_CENTER \
                 + SwitchPairHolderCreator.FOOT_HEIGHT

        switch_pair_holder = SwitchPairHolderCreator()
        for holder_loc in [loc.index, loc.middle, loc.ring, loc.pinkie]:
            for x, y in switch_pair_holder.iter_foot_base_conn_points():
                yield holder_loc * Pos(X=x, Y=y, Z=-z_dist) * SwitchHolderCreatorBase.create_heat_set_insert_hole(screw=data.FLAT_HEAD_SCREW_M2)

        index2_loc = loc.index * Pos(X=SingleSwitchHolderCreator.X_OFFSET)
        for x, y in switch_pair_holder.iter_foot_base_conn_points():
            yield index2_loc * Pos(X=x, Y=y, Z=-z_dist) * SwitchHolderCreatorBase.create_heat_set_insert_hole(screw=data.FLAT_HEAD_SCREW_M2)

    def _create_sphere(self) -> Part:
        loc = SwitchPairHolderFingerLocations()
        sphere_radius = self.SPHERE_RADIUS
        dz = self._dz + self.TUBE_OUTER_RADIUS + sphere_radius + 1
        return loc.middle * Pos(Z=-dz) * Sphere(radius=sphere_radius)

    def _create_sphere_handle(self) -> Part:
        loc = SwitchPairHolderFingerLocations()
        handle_radius = self.SPHERE_HANDLE_RADIUS
        dz = self._dz + self.TUBE_OUTER_RADIUS
        return loc.middle * Pos(Z=-dz) * Cylinder(radius=handle_radius, height=10)

    # def _find_t_in_spline(self, x0: float, spline: Edge) -> float:
    #     """ not used in the moment"""
    #     eps = 1e-3
    #     t1 = 0.0
    #     t2 = 1.0

    #     for i in range(100):
    #         t = (t1 + t2) / 2
    #         p = spline@t
    #         if abs(p.X - x0) < eps:
    #             return t
    #         if p.X < x0:
    #             t2 = t
    #         else:
    #             t1 = t
    #     else: 
    #         raise Exception('t not found in spline')
