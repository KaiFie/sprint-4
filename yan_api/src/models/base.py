from uuid import UUID

import orjson
from pydantic import BaseModel


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class Base(BaseModel):
    uuid: UUID

    class Config:
        allow_population_by_field_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps
