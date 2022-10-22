#!/bin/bash
su -c "ampy --port /dev/ttyUSB0 get log /tmp/log"; cat /tmp/log
