### BEGIN INIT INFO
# Provides: bluetooth-agent
# Required-Start: $remote_fs $syslog bluetooth pulseaudio
# Required-Stop: $remote_fs $syslog
# Default-Start: 2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: Makes Bluetooth discoverable and connectable to 0000
# Description: Start Bluetooth-Agent at boot time.
### END INIT INFO
#! /bin/sh
# /etc/init.d/bluetooth-agent
USER=root
HOME=/root
export USER HOME
case "$1" in
start)
echo "setting bluetooth discoverable"
sudo hciconfig hci0 piscan
start-stop-daemon -S -x /usr/bin/bluetooth-agent -c pi -b -- 0000
echo "bluetooth-agent startet pw: 0000"
;;
stop)
echo "Stopping bluetooth-agent"
start-stop-daemon -K -x /usr/bin/bluetooth-agent
;;
*)
echo "Usage: /etc/init.d/bluetooth-agent {start|stop}"
exit 1
;;
esac
exit 0
