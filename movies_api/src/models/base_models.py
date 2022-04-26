import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    """Fast json dump implementation."""

    return orjson.dumps(v, default=default).decode()


class Base(BaseModel):
    """Base model for representations of Elasticsearch data."""

    uuid: str

    class Config:
        json_loads = orjson.loads
        json_dumps = orjson_dumps
