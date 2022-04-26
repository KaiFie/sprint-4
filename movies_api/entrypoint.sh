#! /usr/bin/env bash
set -e

DEFAULT_GUNICORN_CONF=/usr/src/movies_api/gunicorn_conf.py
export GUNICORN_CONF=${GUNICORN_CONF:-$DEFAULT_GUNICORN_CONF}
export WORKER_CLASS=${WORKER_CLASS:-"uvicorn.workers.UvicornWorker"}

# Start Gunicorn
cd src
exec gunicorn -k "$WORKER_CLASS" -c "$GUNICORN_CONF" "main:app"