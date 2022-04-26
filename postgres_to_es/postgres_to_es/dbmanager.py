import psycopg2
from psycopg2.extensions import connection as _connection
from psycopg2.extras import DictCursor, DictRow
from typing import Any, Mapping, Union

from postgres_to_es.logger import logger
from postgres_to_es.retry import backoff


class DbManager:
    """Class adapter to interact with Postgresql DB."""

    def __init__(self, dsn: Mapping[str, Union[str, int]]) -> None:
        self.dsn: Mapping[str, Union[str, int]] = dsn
        self.conn: _connection
        self.connect()

    @backoff(
        (psycopg2.InterfaceError, psycopg2.OperationalError),
        command='reconnect',
        logger=logger,
    )
    def connect(self) -> None:
        """
        Method to connect to db.
        Returns:
            None
        """
        self.conn = psycopg2.connect(**self.dsn, cursor_factory=DictCursor)
        if not self.is_conn_alive():
            logger.error('Postgres database connection error.')
            raise psycopg2.OperationalError

    def reconnect(self) -> None:
        """
        Method for initialize reconnect to db.
        Returns:
            None
        """
        logger.info('Try to reconnect to db.')
        self.close()
        self.connect()

    def close(self) -> None:
        """
        Close Postgresql DBAPI connection.
        Returns:
            None
        """
        try:
            if self.conn is not None:
                self.conn.close()
        except Exception:
            logger.exception("Error happened on close db connection.")

    def is_conn_alive(self) -> bool:
        """
        Check if Postgresql connection is operational.
        Returns:
            bool
        """
        if self.conn and self.conn.closed == 0:
            with self.conn:
                with self.conn.cursor() as curs:
                    curs.execute('SELECT 1')
                    if curs.fetchone()[0] == 1:
                        logger.info("Postgres db connection operational...")
                        return True
                    else:
                        logger.error("Postgres db connection stale...")
        return False

    @backoff(
        (psycopg2.InterfaceError, psycopg2.OperationalError),
        command='reconnect',
        logger=logger,
    )
    def protected_execute(
            self,
            sql: str,
            *args: tuple[Any, ...],
    ) -> list[DictRow]:
        """
        Execute sql query
        Args:
            sql: str SQL formatted with syntax for psycopg2.
            *args: tuple[Any, ...]  Query arguments.

        Returns: list Query results
        """
        with self.conn as conn:
            with conn.cursor() as curs:
                curs.execute(sql, args)
                return curs.fetchall()
