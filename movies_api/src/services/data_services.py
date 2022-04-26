from typing import Type

import orjson
from aioredis import Redis
from elasticsearch import AsyncElasticsearch, NotFoundError

from core.config import UNIT_CACHE_EXPIRE_IN_SECONDS
from models.data_models import ModelType


class RedisService:
    """Class for maintaining Redis interaction."""

    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def get_from_cache(
            self,
            key: str,
            serialize_model: Type[ModelType],
            serialize_collection: bool = False
    ) -> ModelType | None:
        """
        Get unit data from Redis cache.

        Args:
            key: key of item stored in Redis
            serialize_model: class of item (Film, Person, Genre)
            serialize_collection: bool Serialize collection if True or
            single item if False.
        Returns:
            Pydantic model entity filled with deserialized data from Redis.
        """

        data = await self.redis.get(key)
        if not data:
            return None
        if not serialize_collection:
            result = serialize_model.parse_raw(data)
        else:
            result = [serialize_model(**item) for item in orjson.loads(data)]
        return result

    async def put_to_cache(
        self,
        data: ModelType | list[ModelType],
        key: str = None,
        expire: int = UNIT_CACHE_EXPIRE_IN_SECONDS,
        serialize_collection: bool = False,
    ) -> None:
        """
        Put unit data to Redis cache.

        Args:
            key: key to use for store data in Redis
            data: Type[ModelType] | list[ModelType] One item or collection
            of items.
            serialize_collection: bool Serialize collection if True or single
            item if value False.
            expire: int TTL in seconds.
        """

        if not serialize_collection:
            data = data.json()
        elif serialize_collection and isinstance(data, list):
            data = orjson.dumps([item.dict() for item in data])
        else:
            raise ValueError(
                'Cache candidate is not single instance or not list of models.'
            )
        await self.redis.set(key, data, ex=expire)


class ElasticService:
    """Class for maintaining Elastic interaction."""

    def __init__(self, elastic: AsyncElasticsearch) -> None:
        self.elastic = elastic

    async def search_in_elastic(
            self,
            model: Type[ModelType],
            params: dict
    ) -> list[ModelType] | None:
        """
        Search against Elasticsearch service.

        Args:
            model: Type[ModelType] Pydantic model to serialize search
            results to.
            params: dict Params for search
        Returns:
            List search results as list of Pydantic models 'model'.
        """

        try:
            doc = await self.elastic.search(**params)
        except NotFoundError:
            return None
        return [model(**d['_source']) for d in doc.body['hits']['hits']]

    async def get_from_elastic_by_id(
            self,
            model: Type[ModelType],
            index: str,
            uuid: str
    ) -> ModelType | None:
        """
        Get entity from Elasticsearch by entity id.
        Args:
            model: ModelType Pydantic model to serialize result to.
            index: Index name
            uuid: Entity _id we're looking for.
        Returns:
             ModelType instance.
        """

        try:
            doc = await self.elastic.get(index=index, id=uuid)
        except NotFoundError:
            return None
        return model(**doc['_source'])

    async def get_from_elastic_by_ids(
            self,
            model: Type[ModelType],
            index: str,
            ids: list[str],
    ) -> list[ModelType] | None:
        """
        Get entities from Elasticsearch by entity ids (mget).
        Args:
            model: ModelType Pydantic model to serialize result to.
            index: Index name
            ids: list[str]: Entity _id we're looking for.
        Returns:
             ModelType instance.
        """

        try:
            docs = await self.elastic.mget(index=index, ids=ids)
        except NotFoundError:
            return None
        return [
            model(**doc['_source']) for doc in docs.get('docs', [])
            if doc.get('found')
        ]
