#!/bin/sh

echo "Waiting for Postgres..."
while ! nc -z db 5432; do
  sleep 1
done
echo "Postgres started"

python auth_project/manage.py migrate --noinput
python auth_project/manage.py load_initial_data
python auth_project/manage.py runserver 0.0.0.0:8000