""" Create the foot for the bended big cap switch holder
"""

from typing import Iterator

from ocp_vscode import set_port, show_object
from finger_parts import SingleSwitchHolderCreator


def main():
    holder = BendedSingleSwitchHolderCreator().create()
    show_object(holder)


class BendedSingleSwitchHolderCreator(SingleSwitchHolderCreator):

    def __init__(self):
        super().__init__()
        self.CORRECTIONS.dx += 1  # in direction of holder pair
        self.CORRECTIONS.dy -= 3  # old = 2
        self.CORRECTIONS.dz -= 2  # old = 3


if __name__ == '__main__':
    main()