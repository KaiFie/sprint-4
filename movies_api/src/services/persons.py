from functools import lru_cache
from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from api.v1.utils import PaginateQueryParams
from db.elastic import get_elastic
from db.redis import get_redis
from models.data_models import PersonExt, FilmShort
from services.base_service import BaseService
from services.data_services import ElasticService, RedisService


class PersonService(BaseService):
    """Class to manage logic related to PersonExt entities."""

    elastic_index: str = 'persons'

    async def get_person_by_id(self, person_id: str) -> PersonExt | None:
        """Return PersonExt by its _id."""

        return await self.get_document_by_id(
            person_id,
            PersonExt,
            self.elastic_index,
        )

    async def get_persons_by_ids(
            self, person_ids: [str],
    ) -> list[PersonExt] | None:
        """
        Get persons list by their ids.

        Args:
            person_ids: list[str] list of ids.
        Returns:
            List of entities PersonExt
        """

        persons = await self.elastic.get_from_elastic_by_ids(
            index=self.elastic_index,
            ids=person_ids,
            model=PersonExt,
        )
        return persons

    async def get_persons_by_query(
            self,
            query: str,
            paginate_params: PaginateQueryParams,
    ) -> list[PersonExt] | None:
        """
        Gets persons by query with pagination.

        Args:
            query: str The query string by search
            paginate_params: PaginateQueryParams Paginate params [size, number]
        Returns:
            List of the entity of PersonExt search results.
        """

        page_size = paginate_params.page_size
        page_number = paginate_params.page_number
        if not query:
            return None

        params = {
            'index': self.elastic_index,
            'body': {
                'query': {
                    'bool': {
                        'must': [
                            {'match': {'full_name': query}}
                        ],
                    }
                }
            },
            'from_': page_size * (page_number - 1),
            'size': page_size
        }
        persons = await self.elastic.search_in_elastic(PersonExt, params)
        if not persons:
            return None
        return persons

    async def get_person_films(
            self,
            film_ids: list[str],
    ) -> list[FilmShort] | None:
        """
        Get person's films.

        Args:
            film_ids: list[str]: List of film_ids
        Returns:
            List of entities of FilmShort search results.
        """

        films = await self.elastic.get_from_elastic_by_ids(
            index='movies',
            ids=film_ids,
            model=FilmShort,
        )
        return films


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """
    Init elasticsearch and redis cluster.

    Args:
        redis: Redis Instance of redis
        elastic: AsyncElasticsearch Instance of elastic
    Returns:
        Class object PersonService.
    """

    return PersonService(
        redis=RedisService(redis),
        elastic=ElasticService(elastic)
    )
