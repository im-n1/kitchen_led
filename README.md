# Led kitchen

## 0. Setup
`$ poetry install`

## 1. Create custom firmware with embeded mqtt_as.py
1. Download `mqtt_as.py` file from [MicroPython MQTT](https://github.com/peterhinch/micropython-mqtt/tree/master/mqtt_as)
   and place it into current dir.
2. `docker run --rm -it -v $HOME:$HOME -u $UID -w $PWD larsks/esp-open-sdk bash`
3. `git clone https://github.com/micropython/micropython.git /tmp/micropython`
4. `cp mqtt_as.py /tmp/micropython/ports/esp8266/modules/`
5. `cd /tmp/micropython`
6. `make -C ports/esp8266 submodules`
7. `make -C mpy-cross`
8. `cd ports/esp8266; make`

Compiled firmware is in `build-GENERIC/firmware-combined.bin` file. This is what is gonna
be flashed to the chip. Copy to mounted volume `/home/...` (see $HOME in 1st command) for
easy access to the host machine.

## 2. Flash custom firmware to the chip

1. download MicroPython [here](http://micropython.org/download/esp8266/)
2. install `esptool.py` - `pip install esptool`
3. run `scripts/reflash.sh` script

## 3. Run REPL
`$ ./scripts/rshell.sh`

## 4. Copy program to the chip
`$ ./scripts/put.sh`

## 5. Get program logs
`$ ./scripts/get_log.sh`

## Miscellaneous

### Flash firmware
`$ su -c "esptool.py --port /dev/ttyUSB0 erase_flash ; esptool.py --port /dev/ttyUSB0 --baud 460800 write_flash --flash_size=detect 0 firmware-combined.bin"`

### Open RShell
```
$ su -c "rshell -p /dev/ttyUSB0"
$ cp main.py /boot.py
$ repl
# CTRL + X to exit repl
```

Alternative repl:

```
$ sudo picocom /dev/ttyUSB0 -b115200
```

### Complete wipeout
```
$ poetry shell
$ su -c "esptool.py --port /dev/ttyUSB0 erase_flash"
```

### Get chip info
```
$ poetry shell
$ su -c "esptool.py --port /dev/ttyUSB0 chip_id"
```

### List files
```
$ su -c "ampy --port /dev/ttyUSB0 ls"
```
