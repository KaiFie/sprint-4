from typing import Optional

from elasticsearch import AsyncElasticsearch

es: Optional[AsyncElasticsearch] = None


async def get_elastic() -> AsyncElasticsearch:
    """
    Helper to inject dependency AsyncElasticsearch instance.

    Returns:
        AsyncElasticsearch instance.

    """

    return es
