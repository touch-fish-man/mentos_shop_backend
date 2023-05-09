#!/usr/bin/env bash
# This script is used to redeploy the application
git pull
cp -r config/* /opt/mentos_shop_backend/config/
rm -rf /opt/mentos_shop_backend/dist/*
mkdir -p /opt/mentos_shop_backend/dist
# -f is used to force overwrite
wget  https://zlp-1251420975.cos.accelerate.myqcloud.com/vue/dist.zip -O /tmp/dist.zip
unzip /tmp/dist.zip -d /opt/mentos_shop_backend/dist/
rm -rf /tmp/dist.zip

# no-cache is used to force docker to rebuild the image

docker-compose build --no-cache
docker-compose down
docker-compose up -d