#!/bin/bash


if [[ -z "$1" ]]; then
    echo "Please provide path to a config file."
    exit 1
fi

su -c "ampy --port /dev/ttyUSB0 put main.py /boot.py"
su -c "ampy --port /dev/ttyUSB0 put $1 /config.json"
