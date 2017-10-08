#!/bin/sh
# launcher.sh
# navigate to home directory, then to this directory, then execute python script, then back home.

cd /
cd home/pi/ThreePi
sudo /usr/local/bin/python3.6 Main.py
cd /
