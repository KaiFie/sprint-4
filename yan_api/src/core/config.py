import os
from logging import config as logging_config

from core.logger import LOGGING

# Применяем настройки логирования
logging_config.dictConfig(LOGGING)

# Название проекта. Используется в Swagger-документации
PROJECT_NAME = os.getenv('PROJECT_NAME', 'movies')

# Настройки Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

# Настройки Elasticsearch
ELASTIC_HOST = os.getenv('ELASTIC_HOST', 'localhost')
ELASTIC_PORT = int(os.getenv('ELASTIC_PORT', 9200))

# Корень проекта
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Настройки кеширования
FILM_CACHE_EXPIRE_IN_SECONDS = int(os.getenv('FILM_CACHE_EXPIRE_IN_SECONDS', 300))
GENRE_CACHE_EXPIRE_IN_SECONDS = int(os.getenv('GENRE_CACHE_EXPIRE_IN_SECONDS', 300))
PERSON_CACHE_EXPIRE_IN_SECONDS = int(os.getenv('PERSON_CACHE_EXPIRE_IN_SECONDS', 300))
