import busio


# TRRS standard assignment (ChatGPT):
#   Tip: TX
#   Ring1: RX
#   Ring2: GND
#   Sleeve: VCC


class UartBase:
    _BAUDRATE = 115200  # must be the same for both sides
    _MOUSE_BYTES = b'\x02'
    _KEY_EVENT_BYTES = b'\x03'

    def __init__(self, tx, rx):
        self._uart = busio.UART(tx, rx, baudrate=self._BAUDRATE)

    def wait_for_start(self) -> None:
        raise NotImplementedError()
