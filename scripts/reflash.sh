#!/bin/bash

su -c "esptool.py --port /dev/ttyUSB0 erase_flash ; esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 firmware-combined.bin"
