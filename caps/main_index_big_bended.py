""" A bended big cap for the index finger

One side of this cap is cut off, so the gap between the three index finger caps could reduced.
"""

from typing import Iterator
import copy

from build123d import export_stl, Rot, mirror, Plane, Pos, Box, Part, fillet, Axis, new_edges
from ocp_vscode import show_object

from base import OUTPUT_DPATH
from klp_lame_saddle import CapKind, LameSaddleKeyCapCreator
import klp_lame_data


def main():
    SMALL_CAP_TILT_ANGLE = 15  # 15 degree for each side, s. case/fingerparts.py/SwitchPairHolderCreator.TILT_ANGLE

    pair_holder_back_border = 3.2  # s. keys_holder.BACK_BORDER
    cut_width = 13.9  # s. finger_parts.CUT_WIDTH
    rim_height = klp_lame_data.choc_stem.Z_MAX
    stem_data = klp_lame_data.choc_stem

    single_cap = LameSaddleKeyCapCreator(cap_kind=CapKind.INDEX_FINGER_STD_CUT).create(with_stems=False)

    right_cut_width = cut_width / 2 + 0.5
    left_cut_width = 10  # big enough
    box_width = left_cut_width + right_cut_width
    box_height = 2 * stem_data.Z_MAX
    box_deep = 10  # y-direction - big enough
    dx = box_width / 2 - left_cut_width
    dy = -10  # a rough value is OK

    single_cap -= Pos(X=dx, Y=dy) * Box(box_width, box_deep, box_height)

    y = cut_width/2 + pair_holder_back_border
    cap1 = Pos(Z=-3) * Rot(X=SMALL_CAP_TILT_ANGLE) * Pos(Y=y, Z=3) * single_cap
    cap2 = mirror(cap1, about=Plane.XZ)

    h = 2
    dz = h/2 + klp_lame_data.choc_stem.Z_MAX + 0.3  # 0.3: manual correction height
    conn_box = Pos(Z=dz) * Box(cut_width + 0.7, 16, h)

    conn_box_z_min = dz - h/2
    stems = Part() + list(_iter_stems(z_top=conn_box_z_min))
    conn_box_with_stems = conn_box + stems

    edges = new_edges(conn_box, stems, combined=conn_box_with_stems)
    conn_box_with_fillet = fillet(edges, radius=klp_lame_data.choc_stem.TOP_FILLET_RADIUS)

    result_cap = cap1 + cap2 + conn_box_with_fillet

    if not OUTPUT_DPATH.exists():
        OUTPUT_DPATH.mkdir()
    export_stl(result_cap, OUTPUT_DPATH / 'lame-key-cap-index-big-bended.stl')
    
    show_object(result_cap)


def _iter_stems(z_top: float) -> Iterator[Part]:
    stem_data = klp_lame_data.choc_stem

    z_extra = 0.1  # necessary for top fillets at stem
    stem_dy = 2  # stems should not be centered

    x_len = stem_data.X_MAX - stem_data.X_MIN
    y_len = stem_data.Y_MAX - stem_data.Y_MIN
    z_len = stem_data.Z_MAX - stem_data.Z_MIN + z_extra
    
    stem_box = Pos(Z=-z_len/2 + z_top + z_extra) * Box(x_len, y_len, z_len)
    edges = stem_box.edges().group_by(Axis.Z)[:2]
    stem_box = fillet(edges, radius=klp_lame_data.choc_stem.BOTTOM_FILLET_RADIUS)

    rot = Rot(Z=90)
    x_off = x_len / 2 + stem_data.X_MIN
    yield Pos(Y=stem_dy) * rot * Pos(X=-x_off) * copy.copy(stem_box)
    yield Pos(Y=stem_dy) * rot * Pos(X=x_off) * copy.copy(stem_box)


if __name__ == '__main__':
    main()
