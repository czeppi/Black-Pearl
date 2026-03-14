""" Create switch holder pair for right thumb

There is a little cut off on one side, so that the distance to the trackball can be closer
"""

from ocp_vscode import show
from thumb_switch_holder import ThumbSwitchHolderCreator, KeyboardSide


def main():
    creator = ThumbSwitchHolderCreator(side=KeyboardSide.RIGHT)
    holder = creator.create()  # this includes creating of the stl file
    show(holder)


if __name__ == '__main__':
    main()
