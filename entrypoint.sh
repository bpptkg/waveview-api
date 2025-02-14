#!/bin/sh

DB_HOST=${DB_HOST:-db}

while ! nc -z "$DB_HOST" 5432; do
    echo "Waiting for the database..."
    sleep 1
done

python manage.py migrate

python manage.py collectstatic --no-input

exec "$@"
