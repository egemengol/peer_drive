#!/usr/bin/env bash

# Remote IP
ip_rem=Leni.local
user_rem=egeme

# Local path
path_local=/home/egeme/code/egemenbekir/

# RPi path
path_remote=/home/$user_rem/prog/egemenbekir

rsync -avzhP --exclude-from="./sync_exclude" -e ssh $path_local $user_rem@$ip_rem:$path_remote