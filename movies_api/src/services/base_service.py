from typing import Type

from models.data_models import ModelType
from services.data_services import RedisService, ElasticService


class BaseService:
    """Class for maintaining common class methods"""

    elastic_index: str = None

    def __init__(self, redis: RedisService, elastic: ElasticService) -> None:
        self.redis = redis
        self.elastic = elastic

    async def get_document_by_id(
            self,
            item_id: str,
            serialize_to_model: Type[ModelType],
            index: str
    ) -> ModelType | None:
        """
        Get document from Elasticsearch index by _id.

        Args:
            item_id: str Document _id in Elasticsearch index.
            serialize_to_model: Type[ModelType] Model to serialize data to.
            index: str Elasticsearch index name.
        Returns:
            The document representation as Pydantic Type[ModelType].
        """
        key = self.key_builder(
            index_name=self.elastic_index,
            model_name=serialize_to_model.__name__,
            uuid=item_id,
        )
        item = await self.redis.get_from_cache(
            key=key,
            serialize_model=serialize_to_model,
        )
        if not item:
            item = await self.elastic.get_from_elastic_by_id(
                model=serialize_to_model,
                index=index,
                uuid=item_id
            )
            if not item:
                return None
            await self.redis.put_to_cache(key=key, data=item)
        return item

    def key_builder(
            self,
            index_name: str = '',
            model_name: str = '',
            uuid: str = '',
            separator: str = '::') -> str:
        """
        Build key for data in redis storage.
        Params:
            index_name: str Elasticsearch index name.
            model_name: str Pydantic model representation name.
            uuid: str Entity uuid.
            separator: str Separator. default = '::'

        Returns:
            '{index_name}{separator}{model_name}{separator}{uuid}'
        """
        return f'{index_name}{separator}{model_name}{separator}{uuid}'

    def __repr__(self) -> str:
        return self.__class__.__name__
