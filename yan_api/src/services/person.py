from functools import lru_cache
from typing import Dict, Optional
from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from core.config import PERSON_CACHE_EXPIRE_IN_SECONDS
from db.elastic import get_elastic
from db.redis import get_redis
from models.person import PersonItem, PersonList


class PersonService:
    """
    Класс бизнес логики API персон
    """

    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: UUID) -> Optional[PersonItem]:
        """
        Метод возвращает информацию по персоне по ID
        """
        person = await self._get_person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)

        return person

    async def _get_person_from_elastic(self, person_id: UUID) -> Optional[PersonItem]:
        """
        Метод возвращает информацию по персоне из elasticsearch
        """
        doc = await self.elastic.get('person', person_id)
        return PersonItem(**doc['_source'])

    async def _get_person_from_cache(self, person_id: UUID) -> Optional[PersonItem]:
        """
        Метод возвращает информацию по персоне из redis
        """
        data = await self.redis.get(str(person_id))
        if not data:
            return None
        person = PersonItem.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: PersonItem):
        """
        Метод добавляет ключ по персоне в redis.
        """
        await self.redis.set(str(person.uuid), person.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def get_list(
            self, page: int = 1, size: int = 50,
            sorting: Dict = {'full_name': 'asc'},
            query: Optional[str] = None
    ) -> Optional[PersonList]:
        """
        Метод возвращает список персон со списком фильмов для каждого.
        """
        cache_key = f'person_list_page={page}_size={size}_sort={sorting}'
        if query:
            cache_key = cache_key + '_query=' + str(query)

        persons = await self.get_persons_list_from_cache(cache_key)
        if not persons:
            persons = await self._get_persons_list_from_elastic(page=page, size=size, sorting=sorting, query=query)
            if not persons:
                return None
            await self._put_persons_list_to_cache(cache_key, persons)

        return persons

    async def get_persons_list_from_cache(self, cache_key: str) -> Optional[PersonList]:
        """
        Метод возвращает список персон из Redis и None в случае отсутствия ключа.
        """
        data = await self.redis.get(cache_key)
        if not data:
            return None

        persons = PersonList.parse_raw(data)
        return persons

    async def _put_persons_list_to_cache(self, cache_key: str, persons: PersonList):
        """
        Метод записывает список персон в Redis.
        """
        await self.redis.set(cache_key, persons.json(), expire=PERSON_CACHE_EXPIRE_IN_SECONDS)

    async def _get_persons_list_from_elastic(
            self,
            page: int,
            size: int,
            sorting: Dict,
            query: Optional[str] = None
    ) -> PersonList:
        """
        Метод возвращает список персон из Elastic.
        """
        body = {
            'from': page,
            'size': size,
            "query": {
                "match": {
                    "full_name": {
                        "query": query,
                        "fuzziness": "auto"
                    }
                }
            }
        }
        doc = await self.elastic.search(index='person', body=body)

        items = [PersonItem(**elem['_source']) for elem in doc['hits']['hits']]
        total = doc['hits']['total']['value']

        return PersonList(items=items, total=total)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    """
    Функция создаёт провайдер PersonService
    """
    return PersonService(redis, elastic)
