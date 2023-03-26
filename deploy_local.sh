#!/usr/bin/env bash
# This script is used to deploy the application locally
conda active py38
cp -r .env.sample config/.env
pip install -r requirements.txt
python manage.py reset_db --noinput
python del_migrations.py
python manage.py makemigrations
python manage.py migrate
python mocks/mock_data.py
# kill the process running on port 4000
kill -9 $(lsof -t -i:4000)
nohup  /root/anaconda3/envs/py38/bin/python manage.py runserver 0.0.0.0:4000 &
