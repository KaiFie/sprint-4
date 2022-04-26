import json
from http import HTTPStatus

import elasticsearch
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from postgres_to_es.logger import logger
from postgres_to_es.retry import backoff
from postgres_to_es.state import State


def load_es_mapping(path: str, file_name: str) -> dict:
    if not path or not file_name:
        raise ValueError('Path or filename required.')
    with open(path + file_name) as f:
        data = f.read()
        return json.loads(data)


class ElasticManager:
    """Class adapter for Elasticmanager"""

    def __init__(self, es_url: str) -> None:
        self.client: Elasticsearch = Elasticsearch(es_url)

    @backoff(logger=logger)
    def create_index(self, index_name: str, schema: dict) -> None:
        if not self.client.indices.exists(index=index_name):
            self.client.options(
                ignore_status=HTTPStatus.BAD_REQUEST
            ).indices.create(
                index=index_name,
                mappings=schema['mappings'],
                settings=schema['settings'],
            )

    @backoff(elasticsearch.TransportError, logger=logger)
    def index_doc(
        self,
        index_name: str,
        document: dict,
        doc_id: str,
    ) -> None:
        self.client.create(index=index_name, document=document, id=doc_id)

    @backoff(elasticsearch.TransportError, logger=logger)
    def bulk(self, chunk: list[dict]) -> None:
        """
        Bulk upload.

        Args:
            chunk: list[dict] List of prepared dictionaries for mass index.

        Returns:
            None
        """
        bulk(self.client, chunk)


class ElasticUploader:
    """Upload documents to Elasticsearch index."""

    def __init__(
        self,
        es_manager: ElasticManager,
        state: State,
        table_names: tuple[str, ...],
        index_name: str,
        index_schema: dict,
    ) -> None:
        self.es: ElasticManager = es_manager
        self.state: State = state
        self.table_names: tuple[str, ...] = table_names
        self.index_name: str = index_name
        self.es.create_index(
            index_name=index_name, schema=index_schema
        )

    def bulk_upload(self, chunk: list[dict]) -> None:
        """
        Bulk documents upload.

        Args:
            chunk: list[dict] List of prepared dicts for bulk upload
                              to Elasticsearch.

        Returns: None
        """
        try:
            self.es.bulk(chunk)
        except elasticsearch.helpers.BulkIndexError as e:
            logger.error(e)
            return
        self._update_state()
        logger.info("Chunk of %s docs was indexed successfully.", len(chunk))

    def _update_state(self) -> None:
        """
        Manage state for current processed documents.

        Returns: None

        """
        for table_name in self.table_names:
            this_iteration_ids = self.state.get_state(
                f'{self.index_name}:{table_name}'
                f':current_iteration_selected_ids'
            ) or []

            current_already_processed_ids = self.state.get_state(
                f'{self.index_name}:{table_name}:already_processed_ids',
            ) or []

            current_already_processed_ids.extend(this_iteration_ids)

            self.state.set_state(
                f'{self.index_name}:{table_name}:already_processed_ids',
                [str(id_) for id_ in current_already_processed_ids],
            )
            self.state.set_state(
                f'{self.index_name}:{table_name}:'
                f'current_iteration_selected_ids',
                [],
            )
