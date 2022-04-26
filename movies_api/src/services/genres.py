from functools import lru_cache
from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from api.v1.utils import PaginateQueryParams
from db.elastic import get_elastic
from db.redis import get_redis
from models.data_models import Genre
from services.data_services import ElasticService, RedisService
from services.base_service import BaseService


class GenreService(BaseService):
    elastic_index: str = 'genres'

    async def get_genre_by_id(self, genre_id: str) -> Genre | None:
        """Return Genre by its uuid."""

        return await self.get_document_by_id(
            genre_id,
            Genre,
            self.elastic_index,
        )

    async def get_genres_list(
        self,
        paginate_params: PaginateQueryParams,
    ) -> list[Genre] | None:
        """
        Get list of genres

        Args:
            paginate_params: PaginateQueryParams Paginate params [size, number]

        Returns:
            List of  entities of Genre search results.
        """

        page_size = paginate_params.page_size
        page_number = paginate_params.page_number
        params = {
            'index': self.elastic_index,
        }
        params.update({
            'from_': page_size * (page_number - 1),
            'size': page_size
        })
        genres = await self.elastic.search_in_elastic(Genre, params)
        if not genres:
            return None
        return genres


@lru_cache()
def get_genre_service(
    redis: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    """
    Init elasticsearch and redis cluster.

    Args:
        redis: Redis Instance of redis.
        elastic: AsyncElasticsearch Instance of elastic.
    Returns:
        Class object GenreService.
    """

    return GenreService(
        redis=RedisService(redis),
        elastic=ElasticService(elastic)
    )
