import logging
import aioredis
import uvicorn as uvicorn
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from api.v1 import films, persons, genres
from core import config
from core.logger import LOGGING
from db import elastic
from db import redis
from models.data_models import Tags
from services.cache import CacheAPIResponse
from services.data_services import RedisService


app = FastAPI(
    title=config.PROJECT_NAME,
    docs_url='/api/openapi',
    openapi_url='/api/openapi.json',
    default_response_class=ORJSONResponse,
)


@app.on_event('startup')
async def startup():
    redis.redis = aioredis.from_url(
        f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}',
        encoding='utf-8',
        decode_responses=True,
    )
    elastic.es = AsyncElasticsearch(
        hosts=[
            f'http://{config.ELASTIC_HOST}:{config.ELASTIC_PORT}',
        ]
    )
    redis.cache = aioredis.from_url(
        f'redis://{config.REDIS_HOST}:{config.REDIS_PORT}/2',
        encoding='utf-8',
        decode_responses=True,
    )
    CacheAPIResponse.init(
        redis_service=RedisService(redis=redis.cache),
        expire=config.VIEW_CACHE_EXPIRE_IN_SECONDS,
    )


@app.on_event('shutdown')
async def shutdown():
    await redis.cache.close()
    await redis.redis.close()
    await elastic.es.close()

app.include_router(films.router, prefix='/api/v1/films', tags=[Tags.filmworks])
app.include_router(
    persons.router,
    prefix='/api/v1/persons',
    tags=[Tags.persons]
)
app.include_router(genres.router, prefix='/api/v1/genres', tags=[Tags.genres])

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        log_config=LOGGING,
        log_level=logging.DEBUG,
    )
