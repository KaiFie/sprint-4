#!/bin/bash

echo "Waiting for postgres..."

while ! nc -z $POSTGRES_HOST $POSTGRES_PORT; do
  sleep 0.1
done
echo "PostgreSQL started"

echo "Start ETL service."
python3 postgres_to_es/etl.py || exit 1

exec "$@"