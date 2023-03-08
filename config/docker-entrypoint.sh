#!/bin/bash
/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf
while true
do
	sleep 1
done
