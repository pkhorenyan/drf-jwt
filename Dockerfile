FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y gcc libpq-dev netcat-openbsd && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD sh -c "
  echo 'Waiting for Postgres...' &&
  while ! nc -z db 5432; do sleep 1; done &&
  echo 'Postgres started' &&
  python manage.py migrate --noinput &&
  python manage.py load_initial_data &&
  python manage.py runserver 0.0.0.0:8000
"
