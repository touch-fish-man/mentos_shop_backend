#!/usr/bin/env bash
# This script is used to deploy the application locally

pip install -r requirements.txt
python manage.py reset_db --noinput
python del_migrations.py
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --noinput
python mocks/mock_data.py
python manage.py runserver
