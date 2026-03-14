""" Create only the hotswap socket

This is faster than main_show_all_finger_parts.py
"""

from build123d import export_stl
from ocp_vscode import show

from base import OUTPUT_DPATH
from hot_swap_socket import SwitchSocketCreator


def main():
    create_switch_socket()


def create_switch_socket():
    socket = SwitchSocketCreator().create()
    
    if not OUTPUT_DPATH.exists():
        OUTPUT_DPATH.mkdir()
    export_stl(socket, OUTPUT_DPATH / 'hot-swap-socket.stl')

    show(socket)


if __name__ == '__main__':
    main()
