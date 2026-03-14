""" Create double ball join for the fingers (not the thumbs)
"""

from ocp_vscode import show
from double_ball_join import FingerDoubleBallJoinCreator


def main():
    part = FingerDoubleBallJoinCreator().create()  # this includes creating of the stl files
    show(part)


if __name__ == '__main__':
    main()
