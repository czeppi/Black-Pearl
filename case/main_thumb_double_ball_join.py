""" Create double ball join for the thumbs
"""

from ocp_vscode import show
from double_ball_join import ThumbDoubleBallJoinCreator


def main():
    part = ThumbDoubleBallJoinCreator().create()  # this includes creating of the stl files
    show(part)


if __name__ == '__main__':
    main()
