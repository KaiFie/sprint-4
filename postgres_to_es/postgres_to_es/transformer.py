from abc import ABC, abstractmethod
from typing import Union

from psycopg2.extras import DictRow

from postgres_to_es.esmodels import (
    Genre, Person, MoviesIndexRecord,
    GenresIndexRecord, PersonsIndexRecord,
)


class BaseTransformer(ABC):
    """Base transformer class."""

    @property
    def op_type(self) -> str:
        return "index"

    @property
    @abstractmethod
    def index_name(self):
        raise NotImplementedError

    @abstractmethod
    def transform_row(self, dirty_row: DictRow) -> dict:
        """
        Method to transform row of data to proper shape.
        Args:
            dirty_row: DictRow row of data
        Returns: dict
            Data transformed to proper shape.
        """
        pass

    def transform(self, dirty_chunk: list[DictRow]) -> list[dict]:
        """
        Transform dirty data results returned by PgLoader
        Args:
            dirty_chunk: list[DictRow] PGLoader.load_data results.

        Returns: list[dict]
            List of records ready for Elastic bulk method.
        """
        clear_chunk = []
        for dirty_row in dirty_chunk:
            clear_row = self.transform_row(dirty_row)
            clear_chunk.append(
                self._add_fields_for_bulk_index(clear_row)
            )
        return clear_chunk

    def _add_fields_for_bulk_index(self, data: dict) -> dict:
        """
        Update row data with required fields for Bulk upload to Elastic.
        Args:
            data: dict Row data.
        Returns: dict
            Row with fields ready to send for bulk index.
        """
        data.update(
            {
                '_op_type': self.op_type,
                '_index': self.index_name,
                '_id': data['uuid'],
            }
        )
        return data


class MoviesIndexTransformer(BaseTransformer):
    """Transform logic from dirty PGSQL query results to fill 'movies'
    index for Elasticsearch."""

    @property
    def index_name(self):
        return "movies"

    def _cleanup_agg_data(
        self,
        dirty_data: list[str],
        model: [Person | Genre],
    ) -> tuple[list, list]:
        """
        Convert some tricky formatted fields after Postgresql array_agg.
        Args:
            dirty_data: list[str]

        Returns: list[str], list[Person]
            Normalized list of person names and Person instances.
        """
        persons_models: list[Union[Person, Genre]] = []
        persons_names: list[str] = []
        for dirty_record in dirty_data:
            if dirty_record not in (None, '::'):
                id_, name = dirty_record.split("::")
                persons_names.append(name)
                persons_models.append(
                    model(uuid=id_, name=name)
                )
        return persons_models, persons_names

    def transform_row(self, dirty_row: DictRow) -> dict:
        row_as_dict = dict(dirty_row)
        dirty_directors = row_as_dict.pop('directors')
        dirty_writers = row_as_dict.pop('writers')
        dirty_actors = row_as_dict.pop('actors')
        dirty_genres = row_as_dict.pop('genres')

        es_record = MoviesIndexRecord(**row_as_dict)

        es_record.genre, _ = self._cleanup_agg_data(dirty_genres, Genre)
        es_record.directors, _ = self._cleanup_agg_data(
            dirty_directors, Person
        )
        es_record.writers, es_record.writers_names = self._cleanup_agg_data(
            dirty_writers, Person
        )
        es_record.actors, es_record.actors_names = self._cleanup_agg_data(
            dirty_actors, Person
        )
        return es_record.dict()


class GenresIndexTransformer(BaseTransformer):
    """Data transformer for 'genres' Elasticsearch index."""

    @property
    def index_name(self) -> str:
        return "genres"

    def transform_row(self, dirty_row: DictRow) -> dict:
        es_record = GenresIndexRecord(**dirty_row)
        return es_record.dict()


class PersonsIndexTransformer(BaseTransformer):
    """Data transformer for 'persons' index."""

    @property
    def index_name(self) -> str:
        return "persons"

    def transform_row(self, dirty_row: DictRow) -> dict:
        es_record = PersonsIndexRecord(**dirty_row)
        return es_record.dict()

    def _add_fields_for_bulk_index(self, data: dict) -> dict:
        data = super()._add_fields_for_bulk_index(data)
        data['_id'] = data['uuid'] + ':' + data['role']
        return data
