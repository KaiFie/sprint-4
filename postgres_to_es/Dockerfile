FROM python:3.10.4-slim

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
      netcat=1.10-46 \
  && pip install --no-cache-dir poetry==1.1.6 \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

ENV APP_DIR=/usr/src/postgres_to_es
RUN mkdir -p ${APP_DIR}
WORKDIR $APP_DIR

COPY ./pyproject.toml ./poetry.lock ./

RUN poetry config virtualenvs.create false &&  poetry install --no-interaction --no-ansi --no-dev

COPY . .

RUN chmod +x ./entrypoint.sh
ENV PYTHONPATH "${PYTHONPATH}:${APP_DIR}"
ENTRYPOINT ["./entrypoint.sh"]