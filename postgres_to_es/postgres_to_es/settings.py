from pydantic import (
    BaseSettings,
    Field,
)


class Settings(BaseSettings):
    """Application settings."""

    dbname: str
    host: str = Field('localhost', env=['postgres_host', 'db_host'])
    port: int = 5432
    user: str = Field(..., env=['postgres_user', 'db_user'])
    password: str = Field(..., env=['postgres_password', 'db_password'])

    elasticsearch_url: str = Field(
        'http://localhost:9200',
        env='elasticsearch_url',
    )
    elasticsearch_schema_path: str = './postgres_to_es/assets/'
    limit: int = Field(25, env=['chunk_size', 'limit'])
    scan_delay: int = Field(30, env=['scan_delay', 'etl_sleep'])

    class Config:
        env_file = "./.env.postgres_to_es.develop"
        fields = {
            'dbname': {
                'env': ['postgres_db', 'db_name'],
            },
            'port': {
                'env': ['postgres_port', 'db_port'],
            },

        }


settings = Settings()
pg_dsn = {
    'dbname': settings.dbname,
    'host': settings.host,
    'port': settings.port,
    'user': settings.user,
    'password': settings.password,
}
