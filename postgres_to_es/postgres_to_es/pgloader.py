import datetime
from abc import ABC, abstractmethod

from psycopg2.extras import DictRow

from postgres_to_es.dbmanager import DbManager
from postgres_to_es.state import State


class BaseDataLoader(ABC):
    """Base class for Postgres data loaders."""

    sql_select_ids_template = """
    select id from content.{table} where modified > %s
    {where_clause}
    order by modified
    limit %s
    """

    def __init__(
        self,
        db: DbManager,
        state: State,
        table_names: tuple[str, ...],
        index_name: str = None
    ) -> None:
        self.db: DbManager = db
        self.state: State = state
        self.table_names: tuple[str, ...] = table_names
        self.index_name: str = index_name

    def store_currently_processed_ids(
        self,
        fw_updated_unique_ids: list[str],
        table_name: str,
    ) -> None:
        """
        Store currently processed ids into persistent storage.

        :param fw_updated_unique_ids: list[str]  List of ids to store.
        :param table_name: Teble name, where ids from.
        :return: None
        """
        self.state.set_state(
            f'{self.index_name}:{table_name}:current_iteration_selected_ids',
            list(fw_updated_unique_ids)
        )

    def load_already_processed_ids(self, table_name: str) -> list[str]:
        """
        Read already processed ids list from persistent storage.
        :param table_name: Name of table.
        :return: list[str] List of ids.
        """
        already_processed_ids = self.state.get_state(
            f'{self.index_name}:{table_name}:already_processed_ids'
        ) or []
        if not already_processed_ids:
            self.state.set_state(
                f'{self.index_name}:{table_name}:already_processed_ids', []
            )
        return already_processed_ids

    def get_entities_ids(
        self,
        limit: int,
        modified_from: datetime,
        table_name: str,
        processed_ids: list[str]
    ) -> list[str]:
        """
        Get ids list from arbitrary table.

        Args:
            limit: int  Limit of records to return
            modified_from: datetime Date to use in sql clause
            table_name: str Name of table
            processed_ids: list[str] list Ids of already processed entities.

        Returns: list[str]
            List of genres or person whose were changed.
        """
        if not processed_ids:
            where_clause = ''
            query_args = (modified_from, limit)
        else:
            where_clause = 'and id not in ({})'.format(
                ','.join(['%s' for _ in processed_ids])
            )
            query_args = (modified_from, *processed_ids, limit)
        step_1_sql = self.sql_select_ids_template.format(
            table=table_name,
            where_clause=where_clause,
        )
        entity_ids = self.db.protected_execute(step_1_sql, *query_args)
        return [_['id'] for _ in entity_ids]

    @abstractmethod
    def load_data(
        self,
        modified_from: datetime,
        limit: int = 100
    ) -> list[DictRow]:
        """
        Load data abstract method must be implemented to keep extractor logic.

        Args:
            modified_from: Datetime Date since we need to scan changes.
            limit: int

        Returns:
            List of psycopg2.extras.DictRow records from Postgresql db.
        """
        raise NotImplementedError


class MoviesIndexDataLoader(BaseDataLoader):
    """ Class to extract data to fill 'movies' Elsticsearch index."""

    sql_rich_clause_template = """
    select
        fw.id,
        fw.title,
        fw.description,
        fw.rating imdb_rating,
        fw.modified,
        array_agg(distinct  concat(g.id, '::', g."name")) genres,
        array_agg(distinct concat(p_actor.id, '::', p_actor.full_name)) actors,
        array_agg(distinct concat(p_writer.id, '::', p_writer.full_name)) writers,
        array_agg(distinct concat(p_director.id, '::', p_director.full_name)) directors
    from content.film_work fw
    left outer join content.genre_film_work gfw
        on fw.id = gfw.film_work_id
    left outer join content.genre g
        on gfw.genre_id = g.id
    left outer join content.person_film_work pfw
        on fw.id = pfw.film_work_id
    left outer join content.person p_actor
        on pfw.person_id = p_actor.id and pfw."role" = 'actor'
    left outer join content.person p_writer
        on pfw.person_id = p_writer.id and pfw."role" = 'writer'
    left outer join content.person p_director
        on pfw.person_id = p_director.id and pfw."role" = 'director'
    {where_clause}
    group by
        fw.id
    order by
        fw.modified
    {limit_clause}
    """  # noqa: E501

    sql_select_fw_ids_template = """
    select
        fw.id
    from
        content.film_work fw
    left join content.{table}_film_work pfw on
        pfw.film_work_id = fw.id
    where
        pfw.{table}_id in ({entity_ids})
    order by
        fw.modified
    limit 1000
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, index_name='movies', **kwargs)

    def load_data(
        self,
        modified_from: datetime,
        limit: int = 100
    ) -> list[DictRow]:
        """
        Load data from Postgresql to fill Elasticsearch movies index next.
        Args:
            modified_from: Datetime Date since we need to scan changes.
            limit: int

        Returns:
            List of Filmworks records with aggregated field.
        """
        fw_updated_unique_ids = set()
        for table_name in self.table_names:
            already_processed_ids = self.load_already_processed_ids(table_name)
            fw_updated_unique_ids = fw_updated_unique_ids.union(
                self.get_entities_ids(
                    table_name=table_name,
                    modified_from=modified_from,
                    processed_ids=already_processed_ids,
                    limit=limit,
                )
            )
            self.store_currently_processed_ids(
                fw_updated_unique_ids, table_name
            )
            if modified_from == datetime.datetime.min:  # for first time upload
                break
            if table_name not in ('film_work',):
                fw_updated_unique_ids = fw_updated_unique_ids.union(
                    self.get_filmworks_ids(
                        fw_updated_unique_ids, table_name
                    )
                )
        return self.get_merged_data(fw_updated_unique_ids)

    def get_filmworks_ids(
        self,
        entity_ids: list[str],
        table_name: str,
    ) -> list[str]:
        """
        Get filmworks ids which genre, person entities related to.
        Args:
            entity_ids: list[str] List of ids
            table_name: str Name of table

        Returns: list
            filmworks ids
        """
        if not entity_ids:
            return []
        step2_sql = self.sql_select_fw_ids_template.format(
            table=table_name,
            entity_ids=','.join(['%s' for _ in entity_ids]),
        )
        filmwork_ids = self.db.protected_execute(step2_sql, *entity_ids)
        return [_['id'] for _ in filmwork_ids]

    def get_merged_data(self, fw_ids: list[str]) -> list[DictRow]:
        """
        Get enriched filmwork rows with additional fields attached.
        Args:
            fw_ids: list[str] List of filmwork ids

        Returns:
            list[DictRow]: List of filmwork rows
            with additional fields attached.
        """
        if not fw_ids:
            return []
        step3_sql = self.sql_rich_clause_template.format(
            where_clause='where fw.id in ({})'.format(
                ','.join(['%s' for _ in fw_ids])
            ),
            limit_clause=''
        )
        return self.db.protected_execute(step3_sql, *fw_ids)


class GenresIndexDataLoader(BaseDataLoader):
    """Data loader to fetch data to fill 'genres' index."""

    sql_select_genres_template = """
    select id, name from content.genre where modified > %s
    {where_clause}
    order by modified
    """  # genres < 100, so limit is not needed

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, index_name='genres', **kwargs)

    def get_genres(
        self,
        modified_from: datetime,
        processed_ids: list[str]
    ) -> list[DictRow]:
        """
        Get genres records.
        Args:
            modified_from: Date to use in sql clause
            processed_ids: list Ids of already processed entities.

        Returns: list[DictRow]
            List of genres records.
        """
        if not processed_ids:
            where_clause = ''
            query_args = (modified_from,)
        else:
            where_clause = 'and id not in ({})'.format(
                ','.join(['%s' for _ in processed_ids])
            )
            query_args = (modified_from, *processed_ids,)
        select_genres_sql = self.sql_select_genres_template.format(
            where_clause=where_clause,
        )
        genres = self.db.protected_execute(select_genres_sql, *query_args)
        return genres

    def load_data(
        self,
        modified_from: datetime,
        **kwargs
    ) -> list[DictRow]:
        """
        Load data method
        Args:
            modified_from: Datetime Date since we need to scan changes.
            limit: int

        Returns:
            List of Genres records.
        """
        genres_updated = []
        for table_name in self.table_names:
            already_processed_ids = self.load_already_processed_ids(table_name)
            genres_updated = self.get_genres(
                modified_from=modified_from,
                processed_ids=already_processed_ids,
            )
            self.store_currently_processed_ids(
                [_['id'] for _ in genres_updated], table_name
            )
        return genres_updated


class PersonsIndexDataLoader(BaseDataLoader):
    """Data loader to fetch data to fill 'persons' index."""

    sql_rich_clause_template = """
    select
        p.id "uuid",
        p.full_name,
        pfw."role",
        array_agg(distinct concat(fw.id)) "film_ids"
    from
        "content".person_film_work pfw
    left join "content".film_work fw on
        fw.id = pfw.film_work_id
    left join "content".person p on
        pfw.person_id = p.id
    where
        {where_clause}
    group by
        pfw."role" ,
        p.full_name,
        p.id
    order by p.id
    """

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, index_name='persons', **kwargs)

    def load_data(
        self,
        modified_from: datetime,
        limit: int = 100
    ) -> list[DictRow]:
        """
        Load data method
        Args:
            modified_from: Datetime Date since we need to scan changes.
            limit: int

        Returns:
            List of DictRow records with person data and aggregated film_ids
            field.
        """
        persons_updated_ids = set()
        for table_name in self.table_names:
            already_processed_ids = self.load_already_processed_ids(table_name)
            persons_updated_ids = self.get_entities_ids(
                table_name=table_name,
                modified_from=modified_from,
                processed_ids=already_processed_ids,
                limit=limit,
            )
            self.store_currently_processed_ids(
                persons_updated_ids, table_name
            )
        return self.get_merged_data(persons_updated_ids)

    def get_merged_data(self, persons_ids: list[str]) -> list[DictRow]:
        """
        Get enriched person rows with additional film_ids fields attached
        and grouped by roles.
        Args:
            persons_ids: list[str] List of persons ids

        Returns:
            list[DictRow]: List of persons rows
            with additional fields attached.
        """
        if not persons_ids:
            return []
        sql_text = self.sql_rich_clause_template.format(
            where_clause='pfw.person_id in ({})'.format(
                ','.join(['%s' for _ in persons_ids])
            ),
        )
        return self.db.protected_execute(sql_text, *persons_ids)
