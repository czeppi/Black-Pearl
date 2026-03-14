""" Create the wing for the thumb double ball join
"""

from ocp_vscode import show
from double_ball_join import ThumbHolderWingCreator


def main():
    part = ThumbHolderWingCreator().create()  # this includes creating of the stl file
    show(part)


if __name__ == '__main__':
    main()
