""" Creates all finger parts with skeleton, but without thumb parts
"""

from finger_parts import CaseAssemblyCreator
from ocp_vscode import show


def main():
    creator = CaseAssemblyCreator()
    case_assembly = creator.create()
    show(case_assembly)


if __name__ == '__main__':
    main()
