#!/usr/bin/env bash
# This script is used to redeploy the application
git pull
cp -r config/* /opt/mentos_shop_backend/config/
cp -r dist /opt/mentos_shop_backend/
# no-cache is used to force docker to rebuild the image

docker-compose build --no-cache
docker-compose down
docker-compose up -d

