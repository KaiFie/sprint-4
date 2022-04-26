from typing import Optional

from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError, NotFoundError
from elasticsearch.helpers import bulk
from misc import backoff


class Load:
    """
    The class implements downloading data to Elasticsearch database
    """
    def __init__(self, dsl: dict):
        self.dsl = dsl
        self._es: Optional[Elasticsearch] = None

    @backoff(ConnectionError)
    def _create_connection(self):
        """
        Create new connection to ES
        """
        es = Elasticsearch([self.dsl])
        es.info()
        return es

    @property
    def es(self):
        """
        Return connection to ES
        """
        if self._es is None or self._es.ping() is False:
            self._es = self._create_connection()
        return self._es

    @backoff(ConnectionError)
    def crate_index(self, index: str, body: dict):
        """
        Create index database
        """
        return self.es.indices.create(index=index, body=body)

    @backoff(ConnectionError)
    def load_data(self, data: list):
        """
        Load data to index
        """
        return bulk(self.es, data)

    @backoff(ConnectionError)
    def cat_index(self, index: str):
        """
        Check index is exist
        """
        try:
            return self.es.cat.indices(index=index)
        except NotFoundError:
            return False

