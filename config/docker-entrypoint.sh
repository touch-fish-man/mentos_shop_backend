#!/bin/bash
/usr/local/bin/supervisord -c /etc/supervisor/supervisord.conf
python /opt/mentos_shop_backend/mocks/mock_data.py
while true
do
	sleep 1
done
