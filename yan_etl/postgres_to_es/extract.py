from datetime import datetime
from typing import Optional, Tuple

import psycopg2
from misc import backoff
from models import FilmWorkIndex, GenreIndex, PersonIndex
from psycopg2 import OperationalError
from psycopg2.extensions import connection
from psycopg2.extras import DictCursor


class Extract:
    """
    The class implements unloading data from Postgres database
    """

    def __init__(self, dsl: dict, limit: int):
        self.dsl = dsl
        self.limit = limit
        self._con: Optional[connection] = None

    @backoff(OperationalError)
    def create_connection(self):
        """
        Create connection to db
        """
        return psycopg2.connect(**self.dsl, cursor_factory=DictCursor)

    @property
    def con(self) -> connection:
        """
        Return pg connection
        """
        if self._con is None or self._con.closed:
            self._con = self.create_connection()
        return self._con

    @backoff(OperationalError)
    def fetch_data(self, last_update: datetime, limit: int, index_name: str) -> Tuple[list, Optional[datetime]]:
        """
        Fetch data from database
        """
        with self.con.cursor() as cur:
            with open(f"sql/{index_name}.sql", "r") as sql_file:
                cur.execute(sql_file.read(), (last_update, limit))
            fetch_data = cur.fetchone()
        
        if fetch_data[0] is None:
            return [], None
        if index_name == "movies":
            cls = FilmWorkIndex
        elif index_name == "genre":
            cls = GenreIndex
        else:
            cls = PersonIndex
        data = [cls(**row) for row in fetch_data[0]]
        return data, fetch_data[1]
