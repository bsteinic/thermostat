#!/bin/sh
. /lib/init/vars.sh
. /lib/lsb/init-functions

cd /home/pi/src/thermostat

case "$1" in
    start)
      #flask/bin/python myFSM.py start
      ./run.py > /dev/null &
      exit 0
      ;;
    stop)
      flask/bin/python myFSM.py stop
      kill -9 `pidof '/home/pi/src/thermostat/flask/bin/python'`
      exit 0
      ;;
    *)
      echo "Usage: /etc/init.d/thermostat (start|stop)"
      exit 1
      ;;
esac

