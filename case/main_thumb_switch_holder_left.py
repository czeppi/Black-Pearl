""" Create switch holder pair for left thumb

"""

from ocp_vscode import show
from thumb_switch_holder import ThumbSwitchHolderCreator, KeyboardSide


def main():
    creator = ThumbSwitchHolderCreator(side=KeyboardSide.LEFT)
    holder = creator.create()  # this includes creating of the stl file
    show(holder)


if __name__ == '__main__':
    main()
