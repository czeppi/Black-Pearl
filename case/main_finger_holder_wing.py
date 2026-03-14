""" Create the wing for the finger (not thumb) double ball join
"""

from ocp_vscode import show
from double_ball_join import FingerHolderWingCreator


def main():
    part = FingerHolderWingCreator().create()  # this includes creating of the stl file
    show(part)


if __name__ == '__main__':
    main()
