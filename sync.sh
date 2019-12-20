#!/usr/bin/env bash

# Remote IP
ip_rpi=rpi.local

# Local path
path_local=/home/egeme/code/egemenbekir/

# RPi path
path_remote=/home/pi/prog/egemenbekir

rsync -avzhP --exclude-from="./sync_exclude" -e ssh $path_local pi@$ip_rpi:$path_remote