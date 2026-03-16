
# Firmware

## Why an own firmware

It is very difficult to simulate a 3rd row with the existing keyboard firmwares like QMK or KMK.
Since I am a professional software developer, I decided to write my own. 
I thought that this should be a small piece of work, cause only a subset of the typically firmware is needed (no matrix for example) - that was an error!
All in all it take over three weeks of work.

## Install

### download circuitpython

you can use a pico or a pico2

pico: https://circuitpython.org/board/raspberry_pi_pico_w/
=> adafruit-circuitpython-raspberry_pi_pico_w-en_US-9.2.9.uf2

pico2: https://circuitpython.org/board/raspberry_pi_pico2_w/ 
=> adafruit-circuitpython-raspberry_pi_pico2_w-en_US-9.2.9.uf2

### install circuitpython

- connect Pico to USB while Sel-button is pressed => new drive appears
- drag&drop utf2 file to that drive => a new drive appears

### download library bundle

https://circuitpython.org/libraries => adafruit-circuitpython-bundle-9.x-mpy-20250911.zip

### install library bundle

- copy folders adafruit_bus_device + adafruit_hid
- from adafruit-circuitpython-bundle-9.x-mpy-20250911.zip/adafruit-circuitpython-bundle-9.x-mpy-20250911/lib
- to   [CIRCUIT-Python-drive]:/lib

### copy files to left half (connected with computer)

copy this files from this directory to [CIRCUIT-Python-drive]:/

- mainleft.py -> code.py
- base.py
- button.py
- kbdlayoutdata.py
- keyboardcreator.py
- keyboardhalf.py
- keysdata.py
- macrosdata
- reactions.py
- uart.py
- virtualkeyboard.py

### copy files to right half (only connected with left half)

copy this files from this directory to [CIRCUIT-Python-drive]:/

- mainright.py -> code.py
- base.py
- button.py
- kbdlayoutdata.py
- keyboardhalf.py
- keysdata.py
- pmw3389
- uart.py

## Connection info of the PMW3389

### Pins of the PMW3389

| board |    | color  | description                        |
|-------|----|--------|------------------------------------|
| RST   | RS | brown  | Reset                              |
| GND   | GD | red    | Ground                             |
| MT    | MT | orange | Motion (active low interrupt line) |
| SS    | SS | yellow | Slave Select / Chip Select         |
| SCK   | SC | green  | SPI Clock                          |
| MOSI  | MO | blue   |                                    |
| MISO  | MI | purple |                                    |
| VIN   | VI | gray   | Voltage in up to +5.5V             |

### Connection to the Pico

|           |       |            |
|-----------|-------|------------|
| SPI0_SCK  | Pin 6 | # SPI0_SCK |
| SPI0_MOSI | Pin 7 | # SPI0_TX  |
| SPI0_MISO | Pin 4 | # SPI0_RX  |
	
|           |       |            |
|-----------|-------|------------|
| SPI1_SCK  | Pin 10 | # SPI1_SCK |
| SPI1_MOSI | Pin 11 | # SPI1_TX  |
| SPI1_MISO | Pin 8  | # SPI1_RX  |
	
