#!/usr/bin/env bash
# This script is used to deploy the application locally
# 获取命令参数 is_run, 如果没有传入参数, 则使用默认值 0 作为 is_run
# 如果 is_run 为 1, 则运行 python manage.py runserver
# 如果 is_run 为 0, 则不运行 python manage.py runserver
# 获取命令行参数 port, 如果没有传入参数, 则使用默认值 4000 作为 port
is_run=${1:-0}
port=${2:-4000}
cp -r .env.sample config/.env
pip install -r requirements.txt
python manage.py reset_db -c --noinput
python del_migrations.py
python manage.py makemigrations
python manage.py migrate
python mocks/mock_data.py
if [ $is_run -eq 1 ]; then
    kill -9 $(lsof -i:$port -t)
    python manage.py runserver 0.0.0.0:$port
fi


