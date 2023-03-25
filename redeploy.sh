#!/usr/bin/env bash
# This script is used to redeploy the application
git pull
cp -r config/* /opt/mentos_shop_backend/config/
mkdir -p /opt/mentos_shop_backend/dist
unzip dist/dist.zip -d /opt/mentos_shop_backend/dist

# no-cache is used to force docker to rebuild the image

docker-compose build --no-cache
docker-compose down
docker-compose up -d

