#!/usr/bin/env bash
wget  https://zlp-1251420975.cos.accelerate.myqcloud.com/vue/dist.zip -O /tmp/dist.zip
unzip /tmp/dist.zip -d /opt/mentos_shop_backend/dist/
rm -rf /tmp/dist.zip