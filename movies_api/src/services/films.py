from functools import lru_cache
from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from api.v1.utils import FilterQueryParams, PaginateQueryParams, \
    CommonQueryParams, FilmQueryParams
from db.elastic import get_elastic
from db.redis import get_redis
from models.data_models import Film
from services.data_services import ElasticService, RedisService
from services.base_service import BaseService


class FilmService(BaseService):
    elastic_index: str = 'movies'

    async def get_film_by_id(self, film_params: FilmQueryParams) -> Film | None:
        """
        Get filmwork by uuid.

        Args:
            film_params: FilmQueryParams Filmwork params [uuid].
        Returns:
            Filmwork pydantic model filled with data.
        """

        return await self.get_document_by_id(
            item_id=film_params.film_id,
            serialize_to_model=Film,
            index=self.elastic_index,
        )

    async def get_similar_films(
            self,
            genre_names: list[str]
    ) -> list[Film] | None:
        """
        Get similar films by genres.

        Args:
            genre_names: list[str] List of genres names for search
        Returns:
            List of the entity of Film search results.
        """

        search_field = []
        for g_name in genre_names:
            search_field.append(
                {
                    'nested': {
                        'path': 'genre',
                        'query': {
                            'bool': {
                                'should': {
                                    'match_phrase': {
                                        'genre.name': g_name
                                    }
                                }
                            }
                        }
                    }
                }
            )
        params = {
            'index': self.elastic_index,
            'query': {
                'bool': {
                    'must': search_field
                }
            }
        }
        films = await self.elastic.search_in_elastic(Film, params)
        if not films:
            return None
        return films

    async def get_filtered_sort_films(
            self,
            filter_params: FilterQueryParams,
            paginate_params: PaginateQueryParams,
    ) -> list[Film] | None:
        """
        Get sorted films with pagination.

        Args:
            filter_params: FilterQueryParams Params for filtering
            paginate_params: PaginateQueryParams Paginate params [size, number]
        Returns:
            List of the entity of Film search results.
        """

        sort_field = filter_params.sort
        filter_genre = filter_params.filter_genre
        page_number = paginate_params.page_number
        page_size = paginate_params.page_size

        if sort_field.startswith('-'):
            sort_field = sort_field[1:]
            order = 'desc'
        else:
            order = 'asc'
        params = {
            'index': self.elastic_index,
        }
        if filter_genre:
            params.update({
                'query': {
                    'bool': {
                        'must': {
                            'nested': {
                                'path': 'genre',
                                'query': {
                                    'bool': {
                                        'should': {
                                            'match_phrase': {
                                                'genre.uuid': filter_genre
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }})
        params.update({
            'sort': {
                sort_field: {
                    'order': order
                }
            },
            'from_': page_size * (page_number - 1),
            'size': page_size
        })

        films = await self.elastic.search_in_elastic(Film, params)
        if not films:
            return None
        return films

    async def get_films_by_query(
            self,
            query_params: CommonQueryParams,
            paginate_params: PaginateQueryParams,
    ) -> list[Film] | None:
        """
        Get films by query with pagination.

        Args:
            query_params: CommonQueryParams The query params by search
            paginate_params: PaginateQueryParams Paginate params [size, number]
        Returns:
            List of the entity of Film search results.
        """

        query = query_params.query
        page_size = paginate_params.page_size
        page_number = paginate_params.page_number
        params = {
            'index': self.elastic_index,
            'body': {
                'query': {
                    'bool': {
                        'must': [
                            {
                                'multi_match': {
                                    'query': query,
                                    'fields': ['title', 'description'],
                                }
                            }
                        ],
                    }
                }
            },
            'from_': page_size * (page_number - 1),
            'size': page_size
        }
        films = await self.elastic.search_in_elastic(Film, params)
        if not films:
            return []
        return films


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    """
    Init elasticsearch and redis cluster.

    Args:
        redis: Redis Instance of redis
        elastic: AsyncElasticsearch Instance of elastic
    Returns:
        Class object FilmService.
    """

    return FilmService(
        redis=RedisService(redis),
        elastic=ElasticService(elastic)
    )
