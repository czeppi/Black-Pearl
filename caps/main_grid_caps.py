""" Create cap grid for ordering by JLCPCB

Ordering as grid is cheaper, than order every cap individually.
"""

from build123d import Part, export_stl

from base import OUTPUT_DPATH
from klp_lame_saddle import CapKind, LameKeyCapGridCreator


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
        'b': CapKind.INDEX_FINGER_BIG,      # needed:  2 + 1 reserve =>  3
        }
    cap_kinds = [[cap_kind_map[ch] for ch in col_str] 
                 for col_str in columns_data]
    caps = LameKeyCapGridCreator(cap_kinds=cap_kinds).create()

    # write
    if not OUTPUT_DPATH.exists():
        OUTPUT_DPATH.mkdir()
    export_stl(caps, OUTPUT_DPATH / fname)

    return caps


if __name__ == '__main__':
    main()
