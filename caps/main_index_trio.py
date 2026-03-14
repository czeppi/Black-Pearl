""" Show the three caps for the index finger

To check, if the curves are fitting, show the three caps together.
"""

from build123d import Rot, mirror, Plane, Pos
from ocp_vscode import show_object

from klp_lame_saddle import CapKind, LameSaddleKeyCapCreator


def main():
    create_index_trio()


def create_index_trio() -> None:
    concave_cap = LameSaddleKeyCapCreator(cap_kind=CapKind.INDEX_FINGER_CONCAVE).create()
    big_cap = Rot(Z=180) * LameSaddleKeyCapCreator(cap_kind=CapKind.INDEX_FINGER_BIG).create()

    concave_box = concave_cap.bounding_box()
    big_box = big_cap.bounding_box()

    pair_holder_back_border = 3.2  # s. keys_holder.BACK_BORDER
    cut_width = 13.9  # s. finger_parts.CUT_WIDTH
    cap_height = 4.8  # the height of the cap-bottom

    x = -concave_box.min.X
    y = cut_width/2 + pair_holder_back_border
    z = cap_height - 1.3
    cap1 = Rot(X=15) * Pos(X=x, Y=y, Z=z) * concave_cap
    cap2 = mirror(cap1, about=Plane.XZ)
 
    x = big_box.min.X
    z = cap_height - 1.3 + 6
    cap3 = Pos(X=x, Z=z) * Rot(Y=25) * big_cap

    show_object(cap1 + cap2 + cap3)


if __name__ == '__main__':
    main()
