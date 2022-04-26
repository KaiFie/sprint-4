from pathlib import Path
from typing import Optional

from pydantic import BaseSettings, SecretStr


class Settings(BaseSettings):
    PG_HOST: str
    PG_PORT: int
    PG_DBNAME: str
    PG_PASSWORD: SecretStr
    PG_USER: str
    PG_SCHEMA: str
    LIMIT: Optional[int]
    BULK_TIMER: int
    STATE_FILE_PATH: str
    INDICES_FILE_PATH: str
    ES_HOST: str
    ES_PORT: int
    LOGGER_LEVEL: str

    class Config:
        env_file = Path(__file__).parent.parent / '.env'
        env_file_encoding = 'utf-8'


config = Settings()