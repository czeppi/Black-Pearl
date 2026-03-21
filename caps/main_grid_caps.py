""" Create cap grid for ordering by JLCPCB - without showing

Ordering as grid is cheaper, than order every cap individually.
"""

from typing import Iterator
import copy

from build123d import BoundBox, Cylinder, Part, Pos, Rot, Solid, export_stl

from base import OUTPUT_DPATH
from klp_lame_saddle import CapKind, LameSaddleKeyCapCreator
import klp_lame_data


def main():
    create_grid_caps()


def create_grid_caps() -> None:
    # _create_grid_caps(columns_data=['ob', 'bci'], fname='lame-key-caps-grid-test.stl')

    order_data = [
        ['bcc', 'bcc', 'bcc'],  # 1x
        ['ooo', 'ooo', 'ooo'],  # 2x
        ['iii', 'iii', 'iii'],  # 1x
        ['bcc', 'oooo', 'oooo'],  # metal
    ]

    for i, columns_data in enumerate(order_data):
        fname = f'lame-key-caps-grid{i}.stl'
        print(f'create "{fname}" ...')
        _create_grid_caps(columns_data=columns_data, fname=fname)

    print('ready.')


def _create_grid_caps(columns_data: list[str], fname: str) -> Part:
    # create caps-grid
    cap_kind_map = {
        'o': CapKind.ORIG,                  # needed: 16 + 2 reserve => 18
        'i': CapKind.INDEX_FINGER_STD,      # needed:  8 + 1 reserve =>  9
        'c': CapKind.INDEX_FINGER_CONCAVE,  # needed:  4 + 1 reserve =>  5
        'b': CapKind.INDEX_FINGER_BIG_FLAT,      # needed:  2 + 1 reserve =>  3
        }
    cap_kinds = [[cap_kind_map[ch] for ch in col_str] 
                 for col_str in columns_data]
    caps = LameKeyCapGridCreator(cap_kinds=cap_kinds).create()

    # write
    if not OUTPUT_DPATH.exists():
        OUTPUT_DPATH.mkdir()
    export_stl(caps, OUTPUT_DPATH / fname)

    return caps


class LameKeyCapGridCreator:

    def __init__(self, cap_kinds: list[list[CapKind]]):
        self._cap_kinds = cap_kinds
        self._cap_map: dict[CapKind, Solid] = {}
        self._cap_box_map: dict[CapKind, BoundBox] = {}
        self._column_width: float = -1.0

    def create(self) -> Part:
        grid_data = klp_lame_data.grid
        dist = grid_data.CAP_DISTANCE

        cap_kindes = set(cap_kind for cap_kind_column in self._cap_kinds for cap_kind in cap_kind_column)
        self._cap_map = {cap_kind: LameSaddleKeyCapCreator(cap_kind=cap_kind).create()
                         for cap_kind in cap_kindes}
        self._cap_box_map = {cap_kind: cap.bounding_box()
                             for cap_kind, cap in self._cap_map.items()}
        self._column_width = max(box.max.X - box.min.X
                                 for box in self._cap_box_map.values()) + dist
        self._row_height = max(self._calc_row_height(box=box, cap_kind=cap_kind)
                                for cap_kind, box in self._cap_box_map.items()) + dist

        return Part() + list(self._iter_solids())

    def _calc_row_height(self, box: BoundBox, cap_kind: CapKind) -> float:
        h = box.max.Y - box.min.Y
        if cap_kind == CapKind.INDEX_FINGER_BIG_FLAT:
            return h / 2  # big one will use 2 rows
        else:
            return h

    def _iter_solids(self) -> Iterator[Solid]:
        row_cyl = self._create_row_cylinder()
        col_cyl = self._create_column_cylinder()

        h = self._row_height
        w = self._column_width

        prev_num_rows = 0
        for j, cap_kind_column in enumerate(self._cap_kinds):
            i = 0
            for cap_kind in cap_kind_column:
                cap = self._cap_map[cap_kind]
                x = j * w
                y = i * h

                # horizontal conn cylinder
                if i < prev_num_rows:
                    yield Pos(X=x-w/2, Y=y) * copy.copy(row_cyl)

                # if necessary => 2nd horizontal conn cylinder
                if cap_kind == CapKind.INDEX_FINGER_BIG_FLAT:
                    if i + 1 < prev_num_rows:
                        yield Pos(X=x-w/2, Y=y+h) * copy.copy(row_cyl)

                # vertical conn cylinder
                if i > 0:
                    yield Pos(X=x, Y=y-h/2) * copy.copy(col_cyl)

                # cap
                if cap_kind == CapKind.INDEX_FINGER_BIG_FLAT:
                    y += w / 2

                yield Pos(X=x, Y=y) * copy.copy(cap)

                i += 2 if cap_kind == CapKind.INDEX_FINGER_BIG_FLAT else 1

            prev_num_rows = i

    def _create_row_cylinder(self) -> Solid:
        grid_data = klp_lame_data.grid
        conn_cyl_radius = grid_data.CONN_CYLINDER_RADIUS
        conn_cyl_overlap = grid_data.CONN_CYLINDER_OVERLAP_WITH_CAP
        conn_cyl_height = grid_data.CAP_DISTANCE + 2 * klp_lame_data.saddle.RIM_THICKNESS + 2.0

        return Pos(Z=-conn_cyl_radius + 1.3 + conn_cyl_overlap) * Rot(Y=90) * Cylinder(radius=conn_cyl_radius, height=conn_cyl_height)

    def _create_column_cylinder(self) -> Solid:
        grid_data = klp_lame_data.grid
        conn_cyl_radius = grid_data.CONN_CYLINDER_RADIUS
        conn_cyl_overlap = grid_data.CONN_CYLINDER_OVERLAP_WITH_CAP
        conn_cyl_height = grid_data.CAP_DISTANCE + 2 * klp_lame_data.saddle.RIM_THICKNESS + 4.0

        return Pos(Z=-conn_cyl_radius + 1.3 + conn_cyl_overlap) * Rot(X=90) * Cylinder(radius=conn_cyl_radius, height=conn_cyl_height)


if __name__ == '__main__':
    main()
