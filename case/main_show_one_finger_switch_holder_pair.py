""" Show only one finger switch pair holder

If you only want to see one pair holder, than this is faster than main_show_all_finger_parts.py
"""

from ocp_vscode import show
from finger_parts import SwitchPairHolderCreator


def main():
    create_switch_pair_holder()


def create_switch_pair_holder():
    holder = SwitchPairHolderCreator().create()
    show(holder)


if __name__ == '__main__':
    main()