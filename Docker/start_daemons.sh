#!/bin/bash
couchdb -b
/bin/dbus-daemon --nofork --nopidfile --system 2> /var/log/dbus &
sleep 1
/usr/sbin/avahi-daemon --no-rlimits 2> /var/log/avahi &
sleep 1
python /home/ers/daemon.py --config /etc/ers-node/ers-node.ini 2> /var/log/ers-log &
sleep 1
python /home/web_api.py
