import logging
from functools import wraps
from typing import Type

from models.response_models import ModelResponseType
from models.data_models import ModelType
from services.data_services import RedisService

logger = logging.getLogger(__name__)


class CacheAPIResponse:
    """Cache settings class."""

    _init = False
    _redis_service = None
    _prefix = None
    _expire = None

    @classmethod
    def init(
            cls,
            redis_service: RedisService,
            prefix: str = 'response_cache:',
            expire: int = 3600,
    ):
        if cls._init:
            return
        cls._init = True
        cls._redis_service = redis_service
        cls._prefix = prefix
        cls._expire = expire

    @classmethod
    def get_redis_service(cls) -> RedisService:
        return cls._redis_service

    @classmethod
    def get_prefix(cls) -> str:
        return cls._prefix

    @classmethod
    def get_expire(cls) -> int:
        return cls._expire


def compose_key(prefix, func, *args, **kwargs):
    """
    Compose key from function arguments.

    Args:
        prefix: str Prefix to use
        func: func Function object (FastAPI view function)
        args: Function args parameters
        kwargs: Function kwargs parameters
    Returns:
        The cache key
    """
    kwargs_str = ','.join(
        [str(v) for k, v in kwargs['kwargs'].items()]
    )
    cache_key = (
        f'{prefix}:{func.__module__}::{func.__name__}::{args}::{kwargs_str}'
    )
    return cache_key


def cache(
    serializer_class: Type[ModelType] | Type[ModelResponseType] = None,
    expire: int = None,
    serialize_collection: bool = False,
):
    """
    Cache FastAPI view function decorator.

    Args:
        serializer_class: Type[ModelType] | Type[ModelResponseType]
            Pydantic class to use for serialize cached data.
        expire: int Expire time in seconds
        serialize_collection: bool Boolean flag to set serialize single item
            or collection of classes 'serializer_class'
    Returns:
        Cached result
    """

    def wrapper(func):
        @wraps(func)
        async def inner(*args, **kwargs):
            nonlocal expire
            nonlocal serializer_class
            nonlocal serialize_collection

            copy_kwargs = kwargs.copy()
            request = copy_kwargs.pop('request', None)

            if request.method != 'GET':
                return await func(request, *args, **kwargs)

            expire = expire or CacheAPIResponse.get_expire()
            serialize_collection = serialize_collection
            redis_service = CacheAPIResponse.get_redis_service()
            prefix = CacheAPIResponse.get_prefix()

            cache_key = compose_key(
                prefix,
                func,
                args=args,
                kwargs=copy_kwargs,
            )
            cached_value = await redis_service.get_from_cache(
                key=cache_key,
                serialize_model=serializer_class,
                serialize_collection=serialize_collection,
            )
            if cached_value is not None:
                logger.info('Cache key %s hit !', cache_key)
                return cached_value
            execution_result = await func(*args, **kwargs)
            await redis_service.put_to_cache(
                data=execution_result,
                key=cache_key,
                serialize_collection=serialize_collection,
                expire=expire
            )
            return execution_result
        return inner
    return wrapper
