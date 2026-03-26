from __future__ import annotations
import math

from build123d import export_stl, JernArc, Line, Rectangle, Vector, GeomType
from build123d import Box, Part, Pos, Rot, Cylinder, Sphere, Circle, revolve, Axis, Plane, RegularPolygon, extrude, Compound, fillet, Solid, Edge, sweep
from ocp_vscode import show

from base import OUTPUT_DPATH, mm, Degree
import data


WRITE_ENABLED = True  # set this to False for only view the result


class DoubleBallJoinCreator:
    BELT_FACTOR = 0.8  # = belt_radius / sphere_radius
    SPHERE_COMPLETENESS = 0.70
    SCREW = data.HEXAGON_SCREW_M6
    HALVES_GAP = 2.0  # cut a litte more than a half for better tension
    TOLERANCE = 0.1  # make sphere + cylinder a litte bigger    

    def __init__(self, name_prefix: str, sphere_radius: mm, sphere_dist: mm, handle_radius: mm, thickness: mm, bend_angle: Degree,
                 sphere_hole_offset: mm, screw_cylinder_length_nut_side_offset=0.0, screw_cylinder_length_screw_side_offset=0.0):
        self._name_prefix = name_prefix
        self._sphere_radius = sphere_radius
        self._sphere_dist = sphere_dist
        self._handle_radius = handle_radius
        self._thickness = thickness
        self._bend_angle = bend_angle 
        self._sphere_hole_offset = sphere_hole_offset
        self._screw_cylinder_length_nut_side_offset = screw_cylinder_length_nut_side_offset
        self._screw_cylinder_length_screw_side_offset = screw_cylinder_length_screw_side_offset
    
    def create(self) -> Compound:
        if self._bend_angle == 0:
            holder_half1, holder_half2 = self._create_straight_halves()
        else:
            holder_half1, holder_half2 = self._create_bend_halves()

        holder_half1.label = 'half1'
        holder_half2.label = 'half2'

        if WRITE_ENABLED:
            if not OUTPUT_DPATH.exists():
                OUTPUT_DPATH.mkdir()

            export_stl(holder_half1, OUTPUT_DPATH / f'{self._name_prefix}-double-ball-holder1.stl')
            export_stl(holder_half2, OUTPUT_DPATH / f'{self._name_prefix}-double-ball-holder2.stl')

        return Compound(label="double-ball-join", children=[holder_half1, holder_half2])
    
    def _create_straight_halves(self) -> tuple[Solid, Solid]:
            holder = self._create_straight_holder()

            a = 100  # must only big enough
            x = a/2 - self.HALVES_GAP / 2
            holder_half1 = holder - Pos(X=x) * Box(a, a, a)
            holder_half2 = holder - Pos(X=-x) * Box(a, a, a)

            return holder_half1, holder_half2

    def _create_straight_holder(self) -> Solid:
        r1 = self._sphere_radius + self._thickness  # outer sphere radius
        d_2 = self._sphere_dist / 2
        torus_minor_radius = self._calc_torus_minor_radius()
        belt_radius = self.BELT_FACTOR * r1
        cyl_radius = self._calc_vertical_cylinder_radius(torus_minor_radius)

        upper_outer_sphere = Pos(0, 0, d_2) * Sphere(r1)
        upper_inner_sphere = Pos(0, 0, d_2) * Sphere(self._sphere_radius)
        lower_outer_sphere = Pos(0, 0, -d_2) * Sphere(r1)
        lower_inner_sphere = Pos(0, 0, -d_2) * Sphere(self._sphere_radius)

        z3 = d_2 + self._sphere_hole_offset
        holder_r = self._handle_radius + 0.5  # add some tolerance
        upper_sphere_holder_neg_cylinder = Pos(0, 0, z3) * Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        lower_sphere_holder_neg_cylinder = Pos(0, 0, -z3) * Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        upper_sphere_holder_neg_box = Pos(0, 0, 50 + z3) * Box(2 * holder_r, 100, 100)
        lower_sphere_holder_neg_box = Pos(0, 0, -50 + -z3) * Box(2 * holder_r, 100, 100)

        h = (d_2 - r1) + (self.SPHERE_COMPLETENESS * 2 * r1)
        upper_neg_box = Pos(0, 0, h + 50) * Box(100, 100, 100)
        lower_neg_box = Pos(0, 0, -h - 50) * Box(100, 100, 100)

        conn_cylinder = Cylinder(radius=cyl_radius, height=self._sphere_dist)
        torus = revolve(Plane.XZ * Pos(belt_radius + torus_minor_radius, 0) * Circle(torus_minor_radius), Axis.Z)

        # screw part
        screw = self.SCREW
        cyl_len = 2 * r1  + self._screw_cylinder_length_nut_side_offset + self._screw_cylinder_length_screw_side_offset
        dz = -r1 - self._screw_cylinder_length_screw_side_offset
        loc = Rot(Y=90) * Pos(Z=dz)
        screw_head_radius = screw.head_radius + self.TOLERANCE
        screw_radius = screw.radius + self.TOLERANCE
        screw_cylinder = loc * Pos(Z=cyl_len/2) * Cylinder(radius=screw_head_radius + self._thickness, height=cyl_len)
        screw_hole = loc * Pos(Z=cyl_len/2) * Cylinder(radius=screw_radius, height=cyl_len)
        screw_head = loc * extrude(Plane.XY * RegularPolygon(radius=screw_head_radius, side_count=6), amount=screw.head_height)

        # all together
        part = upper_outer_sphere + conn_cylinder + lower_outer_sphere - torus - upper_neg_box - lower_neg_box \
               - upper_sphere_holder_neg_cylinder - upper_sphere_holder_neg_box - lower_sphere_holder_neg_cylinder - lower_sphere_holder_neg_box \
               + screw_cylinder - screw_hole - upper_inner_sphere - lower_inner_sphere - screw_head
        return part
    
    def _calc_torus_minor_radius(self) -> mm:
        return self._create_conn_circle_calculator().calc_radius()
    
    def _calc_vertical_cylinder_radius(self, torus_radius: mm) -> mm:
        return self._create_conn_circle_calculator().calc_width_of_conn_lines(torus_radius)
    
    def _create_conn_circle_calculator(self) -> ConnCircleCalculator:
        circles_radius = self._sphere_radius + self._thickness  # outer radius
        return ConnCircleCalculator(circles_radius=circles_radius,
                                    circles_dist=self._sphere_dist,
                                    belt_radius=self.BELT_FACTOR * circles_radius)
    
    def _create_bend_halves(self) -> tuple[Solid, Solid]:
        bend_radius = self._calc_bend_radius()

        holder = self._create_bend_holder(bend_radius)

        a = 100  # must only big enough
        b = 500  # must bigger than a

        neg1 = Rot(X=90) * Cylinder(bend_radius + self.HALVES_GAP / 2, height=a)
        neg2 = Box(b, b, b) - Rot(X=90) * Cylinder(bend_radius - self.HALVES_GAP / 2, height=a)

        holder_half1 = holder - neg1
        holder_half2 = holder - neg2
        return holder_half1, holder_half2
    
    def _calc_bend_radius(self) -> mm:
        #bend_radius = self._create_conn_circle_calculator().calc_radius()
        #return bend_radius

        alpha = math.radians(self._bend_angle)
        d = self._sphere_dist
        r = d/2 / math.sin(alpha/2)
        return r

    def _create_bend_holder(self, bend_radius: mm) -> Solid:
        bend_angle = self._bend_angle
        r1 = self._sphere_radius + self._thickness  # outer sphere radius
        d_2 = self._sphere_dist / 2

        bend_path = self._create_bend_path(bend_radius)
        mid_part = self._create_bend_middle_part(path=bend_path)

        lower_outer_sphere = Pos(bend_path@0) * Sphere(radius=r1)
        lower_inner_sphere = Pos(bend_path@0) * Sphere(self._sphere_radius)
        upper_outer_sphere = Pos(bend_path@1) * Sphere(radius=r1)
        upper_inner_sphere = Pos(bend_path@1) * Sphere(self._sphere_radius)

        # body
        part = lower_outer_sphere + mid_part + upper_outer_sphere
        part = fillet(part.edges(), radius=10)

        # cut end of spheres
        a = 200  # must only big enough
        h = self.SPHERE_COMPLETENESS * 2 * r1 - r1
        lower_neg_box = Pos(0, 0, -h - a/2) * Box(a, a, a)
        upper_neg_box = Rot(Y=-bend_angle) * Pos(0, 0, h + a/2) * Box(a, a, a)
        part = part - lower_neg_box - upper_neg_box

        # holes at end of spheres
        z3 = self._sphere_hole_offset
        a = 2 * r1  # must only big enough
        holder_r = self._handle_radius + 0.5  # add some tolerance
        lower_sphere_holder_loc = Pos(bend_radius, 0, -z3)
        lower_sphere_holder_neg_cylinder = Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        lower_sphere_holder_neg_box = Pos(Z=-a/2) * Box(2 * holder_r, a, a)
        lower_sphere_holder_neg_part = lower_sphere_holder_loc * (lower_sphere_holder_neg_cylinder + lower_sphere_holder_neg_box)

        upper_sphere_holder_loc = Rot(Y=-bend_angle) * Pos(bend_radius, 0, z3)
        upper_sphere_holder_neg_cylinder = Rot(X=90) * Cylinder(holder_r, height=2 * r1)
        upper_sphere_holder_neg_box = Pos(Z=a/2) * Box(2.01 * holder_r, a, a)  # !! ERROR - with "Box(2 * holder_r, a, a)" it does not work !!
        upper_sphere_holder_neg_part = upper_sphere_holder_loc * (upper_sphere_holder_neg_cylinder + upper_sphere_holder_neg_box)

        part = part - upper_sphere_holder_neg_part - lower_sphere_holder_neg_part

        # screw part
        screw = self.SCREW
        cyl_len = 2 * r1  + self._screw_cylinder_length_nut_side_offset + self._screw_cylinder_length_screw_side_offset
        screw_head_radius = screw.head_radius + self.TOLERANCE
        screw_radius = screw.radius + self.TOLERANCE
        screw_cylinder = Pos(Z=cyl_len/2) * Cylinder(radius=screw_head_radius + self._thickness, height=cyl_len)
        screw_hole = Pos(Z=cyl_len/2) * Cylinder(radius=screw_radius, height=cyl_len)
        screw_head = extrude(Plane.XY * RegularPolygon(radius=screw_head_radius, side_count=6), amount=screw.head_height)
        screw_neg = screw_hole + upper_inner_sphere + lower_inner_sphere + screw_head

        dx = -r1 - self._screw_cylinder_length_nut_side_offset + bend_radius
        loc = Rot(Y=-bend_angle/2) * Pos(X=dx) * Rot(Y=90)
        part = part + loc * screw_cylinder - loc * screw_neg

        # remove inner spheres
        part = part - lower_inner_sphere - upper_inner_sphere

        return part
    
    def _create_bend_path(self, bend_radius: mm) -> Edge:
        path = Plane.XZ * Edge.make_circle(radius=bend_radius, start_angle=0, end_angle=self._bend_angle)
        return path
    
    def _create_bend_middle_part(self, path: Edge) -> Solid:
        r1 = self._sphere_radius + self._thickness  # outer sphere radius
        belt_radius = self.BELT_FACTOR * r1

        profile_template1 = Circle(belt_radius)
        profile_template2 = Circle(belt_radius)

        start_plane = Plane(origin=path@0, z_dir=(0, 0, 1), x_dir=(1, 0, 0))
        start_profile = start_plane * profile_template1

        mid_tangent = path%0.5
        mid_x_dir = mid_tangent.cross(Vector(0, 0, 1)).normalized()
        mid_plane = Plane(origin=path@0.5, z_dir=mid_tangent, x_dir=mid_x_dir)
        mid_profile = mid_plane * profile_template2

        end_tangent = path%1
        end_x_dir = end_tangent.cross(Vector(0, 0, 1)).normalized()
        end_plane = Plane(origin=path@1, z_dir=end_tangent, x_dir=end_x_dir)
        end_profile = end_plane * profile_template1

        return sweep([start_profile, mid_profile, end_profile], path=path, multisection=True)
    

class ConnCircleCalculator:
    """ given: 2 circles;  wanted: a circle, which connect the 2 circles smoothly

          (   )             # 1st given circle
           )x(----R----x    # wanted circle with x as center
          (   )             # 2nd given circle
        
          d: distance between centers of 2 circles
          r: radius of the 2 circles
          b: radius at belt (= BELT_FACTOR * r)
        
          (d/2)^2 + (b + R)^2 = (r + R)^2
        
        =>
              d^2 + 4 (b^2 - r^2)
          R = -------------------
                 8 (r - b)
    """

    def __init__(self, circles_radius: mm, circles_dist: mm, belt_radius: mm):
        self._circles_radius = circles_radius  # radius of given 2 circles
        self._circles_dist = circles_dist   # distance of the centers of 2 given circles
        self._belt_radius = belt_radius  # must smaller than circles_radius

    def calc_radius(self) -> mm:
        d = self._circles_dist
        r = self._circles_radius
        b = self._belt_radius
        
        return (d**2 + 4 * (b**2 - r**2)) / (8 * (r - b))    
    
    def calc_width_of_conn_lines(self, conn_circle_radius: mm) -> mm:
        """
          (   )             # 1st given circle
           ---              # conn line
           )x(----R----x    # wanted circle with x as center
           ---              # conn line
          (   )             # 2nd given circle
 
            x-r1-                     # x: center of 1st given center
                 -|--                 # |: conn point between 1st given circle and conn circle
                  |  -r2-
                  |      ----
            x-----|--------------x    # left x: middle between centers of given circles, right x: center of conn circle
                                      #     distance between x-points: belt_radius + conn_circle_radius
        """
        r1 = self._circles_radius
        b = self._belt_radius
        r2 = conn_circle_radius

        return r1 / (r1 + r2)  * (b + r2)


class FingerDoubleBallJoinCreator(DoubleBallJoinCreator):
    NAME_PREFIX = 'finger'
    SPHERE_RADIUS = 12
    HANDLE_RADIUS = 7
    SPHERE_DIST = 35  # orig: 68.0 - 24.0 = 44.0
    THICKNESS = 4
    BEND_ANGLE = 0  # 30
    SPHERE_HOLE_OFFSET = 5
    SCREW_CYLINDER_LENGTH_NUT_SIDE_OFFSET = 0  # differenzce to outer sphere radius (with -1 the wing is hitting the join)
    SCREW_CYLINDER_LENGTH_SCREW_SIDE_OFFSET = -1  # differenzce to outer sphere radius (make smaller, otherwide 30mm screw is too short - and 40mm too long)

    def __init__(self):
        super().__init__(name_prefix=self.NAME_PREFIX, sphere_radius=self.SPHERE_RADIUS, handle_radius=self.HANDLE_RADIUS, sphere_dist=self.SPHERE_DIST, 
                         thickness=self.THICKNESS, bend_angle=self.BEND_ANGLE, sphere_hole_offset=self.SPHERE_HOLE_OFFSET,
                         screw_cylinder_length_nut_side_offset=self.SCREW_CYLINDER_LENGTH_NUT_SIDE_OFFSET,
                         screw_cylinder_length_screw_side_offset=self.SCREW_CYLINDER_LENGTH_SCREW_SIDE_OFFSET)


class ThumbDoubleBallJoinCreator(DoubleBallJoinCreator):
    NAME_PREFIX = 'thumb'
    SPHERE_RADIUS = 10
    HANDLE_RADIUS = 6
    SPHERE_DIST = 30
    THICKNESS = 3
    BEND_ANGLE = 0
    SPHERE_HOLE_OFFSET = 3
    SCREW_CYLINDER_LENGTH_NUT_SIDE_OFFSET = -1
    SCREW_CYLINDER_LENGTH_SCREW_SIDE_OFFSET = -1

    def __init__(self):
        super().__init__(name_prefix=self.NAME_PREFIX, sphere_radius=self.SPHERE_RADIUS, handle_radius=self.HANDLE_RADIUS, sphere_dist=self.SPHERE_DIST, 
                         thickness=self.THICKNESS, bend_angle=self.BEND_ANGLE, sphere_hole_offset=self.SPHERE_HOLE_OFFSET,
                         screw_cylinder_length_nut_side_offset=self.SCREW_CYLINDER_LENGTH_NUT_SIDE_OFFSET,
                         screw_cylinder_length_screw_side_offset=self.SCREW_CYLINDER_LENGTH_SCREW_SIDE_OFFSET)


class HolderWingCreator:
    TOLERANCE = 0.1
    FILLET_RADIUS = 0.75

    def _create(self, name_prefix: str, wing_length: mm, wing_width: mm, wing_height: mm, screw: data.HexagonScrew, 
                heat_set_length: mm, screw_hole_length: mm, hole_cylinder_thickness: mm) -> Solid:
        r1 = screw.head_set_insert_radius
        r2 = screw.radius + self.TOLERANCE
        r3 = r1 + hole_cylinder_thickness
        dz = wing_width / 2
        tube_gap = 2
        cyl_len = wing_width + tube_gap
        hole_outer_cylinder = Pos(Z=cyl_len/2) * Cylinder(r3, cyl_len)
        heat_set_hole = Pos(Z=heat_set_length / 2) * Cylinder(r1, heat_set_length)
        screw_hole = Pos(Z=screw_hole_length / 2) * Cylinder(r2, screw_hole_length)
        wing_box = Pos(Z=dz + tube_gap) * Box(2 * (wing_length + r3), wing_height, wing_width)

        # !! "fillet((wing_box + hole_outer_cylinder).edges(), self.FILLET_RADIUS)" won't work !!
        fillet_cylinder = fillet(hole_outer_cylinder.edges(), self.FILLET_RADIUS)
        body_raw = fillet_cylinder + wing_box

        edges = [edge for edge in body_raw.edges() if edge.geom_type == GeomType.LINE]
        fillet_body = fillet(edges, self.FILLET_RADIUS)

        part = fillet_body - screw_hole - heat_set_hole
        if WRITE_ENABLED:
            export_stl(part, OUTPUT_DPATH / f'{name_prefix}-double-ball-wing.stl')

        return part
    

class FingerHolderWingCreator(HolderWingCreator):
    WING_LENGTH = 12  # x-dir
    WING_WIDTH = 10  # z-dir
    WING_HEIGHT = 5  # y-dir
    SCREW = data.HEXAGON_SCREW_M6
    HEAT_SET_LENGTH = 8
    SCREW_HOLE_LENGTH = 9
    HOLE_CYLINDER_THICKNESS = 3

    def create(self) -> Part:
        return self._create(name_prefix='finger',
                            wing_length=self.WING_LENGTH, 
                            wing_width=self.WING_WIDTH,
                            wing_height=self.WING_HEIGHT,
                            screw=self.SCREW,
                            heat_set_length=self.HEAT_SET_LENGTH,
                            screw_hole_length=self.SCREW_HOLE_LENGTH,
                            hole_cylinder_thickness=self.HOLE_CYLINDER_THICKNESS)


class ThumbHolderWingCreator(HolderWingCreator):
    WING_LENGTH = 10  # x-dir
    WING_WIDTH = 10  # z-dir
    WING_HEIGHT = 4  # y-dir
    SCREW = data.HEXAGON_SCREW_M6
    HEAT_SET_LENGTH = 8
    SCREW_HOLE_LENGTH = 9
    HOLE_CYLINDER_THICKNESS = 3

    def create(self) -> Part:
        return self._create(name_prefix='thumb',
                            wing_length=self.WING_LENGTH, 
                            wing_width=self.WING_WIDTH,
                            wing_height=self.WING_HEIGHT,
                            screw=self.SCREW,
                            heat_set_length=self.HEAT_SET_LENGTH,
                            screw_hole_length=self.SCREW_HOLE_LENGTH,
                            hole_cylinder_thickness=self.HOLE_CYLINDER_THICKNESS)
