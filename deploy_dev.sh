#!/usr/bin/env zsh
# This script is used to deploy the application locally
cp -r .env.sample config/.env
export DJANGO_ENV=dev
/root/anaconda3/envs/py38/bin/pip install -r requirements.txt
/root/anaconda3/envs/py38/bin/python manage.py reset_db --noinput
/root/anaconda3/envs/py38/bin/python del_migrations.py
/root/anaconda3/envs/py38/bin/python manage.py makemigrations
/root/anaconda3/envs/py38/bin/python manage.py migrate

# kill the process running on port 4000
kill -9 $(lsof -t -i:4000)
# 删除已经存在的django screen
screen -X -S django quit
# 创建django screen
screen -dmS django
# 在django screen中运行命令
screen -S django -p 0 -X stuff "/root/anaconda3/envs/py38/bin/python mocks/mock_data.py && export DJANGO_ENV=dev && nohup  /root/anaconda3/envs/py38/bin/python manage.py runserver 0.0.0.0:4000 &";
screen -S django -p 0 -X stuff $'\n';