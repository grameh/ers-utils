#!/bin/bash
couchdb -b
/bin/dbus-daemon --nofork --nopidfile --system 2> /var/log/dbus &
sleep 1
/usr/sbin/avahi-daemon --no-rlimits 2> /var/log/avahi &
python /home/ers/daemon.py --config /etc/ers-node/ers-node.ini
/bin/bash
