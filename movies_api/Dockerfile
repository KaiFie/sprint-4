FROM python:3.10.4-slim

RUN pip install --no-cache-dir poetry==1.1.6

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_DIR=/usr/src/movies_api
WORKDIR $APP_DIR

COPY ./pyproject.toml ./poetry.lock ./

RUN poetry config virtualenvs.create false &&  poetry install --no-interaction --no-ansi --no-dev

COPY ./src ./src
COPY  ./entrypoint.sh ./
COPY ./gunicorn_conf.py ./

RUN chmod +x ./entrypoint.sh
ENV PYTHONPATH "${PYTHONPATH}:${APP_DIR}"
EXPOSE 8000
ENTRYPOINT ["./entrypoint.sh"]