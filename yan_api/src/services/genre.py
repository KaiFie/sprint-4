from functools import lru_cache
from typing import List, Optional, Tuple
from uuid import UUID

import orjson
from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from core.config import GENRE_CACHE_EXPIRE_IN_SECONDS
from db.elastic import get_elastic
from db.redis import get_redis
from models.genre import GenreItem


class GenreService:
    """
    Business logic class API Genre
    """
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: UUID) -> Optional[GenreItem]:
        """
        Find genre by uuid
        """
        genre = await self._genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)

        return genre

    async def _get_genre_from_elastic(self, genre_id: UUID) -> Optional[GenreItem]:
        """
        Get data from elastic
        """
        doc = await self.elastic.get('genre', genre_id)
        return GenreItem(**doc['_source'])

    async def _genre_from_cache(self, genre_id: UUID) -> Optional[GenreItem]:
        """
        Get data from redis
        """
        data = await self.redis.get(str(genre_id))
        if not data:
            return None
        genre = GenreItem.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: GenreItem):
        """
        Put data to redis
        """
        await self.redis.set(str(genre.uuid), genre.json(), expire=GENRE_CACHE_EXPIRE_IN_SECONDS)

    async def get_list_genre(self, size) -> Optional[Tuple[List[GenreItem], int]]:
        """
        Get genre list
        """
        genres, count = await self._get_genre_list_from_cache(size)
        if not genres:
            genres, count = await self._get_genre_list_from_elastic(size)
            if not genres:
                return None
            await self._put_genre_list_to_cache(genres, size, count)
        return genres, count

    async def _get_genre_list_from_elastic(self, size):
        """
        Get data from elastic
        """
        genre_list = await self.elastic.search(index='genre', body={'query': {'match_all': {}}}, size=size)
        return [GenreItem(**genre['_source']) for genre in genre_list['hits']['hits']], genre_list['hits']['total']['value']

    async def _get_genre_list_from_cache(self, size: int) -> Tuple:
        """
        Get data from redis
        """
        data = await self.redis.get(f'genre_list_size={size}')
        count = await self.redis.get('count_genres')
        if not data:
            return None, None
        genres = [GenreItem.parse_raw(item) for item in orjson.loads(data)]
        return genres, int(count)

    async def _put_genre_list_to_cache(self, genres: List[GenreItem], size: int, count: int):
        """
        Put data to redis
        """
        await self.redis.set(f'genre_list_size={size}', orjson.dumps([item.json() for item in genres]),
                             expire=GENRE_CACHE_EXPIRE_IN_SECONDS)
        await self.redis.set('count_genres', count, expire=GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)
