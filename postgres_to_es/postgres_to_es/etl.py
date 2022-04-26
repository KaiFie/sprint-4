import datetime
import time

from postgres_to_es.dbmanager import DbManager
from postgres_to_es.esmanager import (
    ElasticManager,
    ElasticUploader,
    load_es_mapping,
)
from postgres_to_es.logger import logger
from postgres_to_es.pgloader import (
    MoviesIndexDataLoader,
    GenresIndexDataLoader,
    PersonsIndexDataLoader,
)
from postgres_to_es.settings import pg_dsn, settings
from postgres_to_es.state import JsonFileStorage, State
from postgres_to_es.transformer import (
    MoviesIndexTransformer,
    GenresIndexTransformer,
    PersonsIndexTransformer,
)


class ETL:
    """Extract Transform Load control class."""

    table_names: tuple = ('film_work', 'person', 'genre')

    def scan_tables(
        self,
        db: DbManager,
        state: State,
        es_manager: ElasticManager,
        chunk_size: int
    ) -> None:
        """
        Manage index, scan tables changes by modified field.
        Args:
            db: DbManager Database connection manager
            state: State State class instance.
            es_manager: ElasticManager
            chunk_size: int Query limit, how many records to select at once.

        Returns:
            None
        """
        scan_data = (
            (
                "movies",
                self.table_names,
                MoviesIndexTransformer,
                MoviesIndexDataLoader
            ),
            (
                "genres",
                ("genre",),
                GenresIndexTransformer,
                GenresIndexDataLoader,
            ),
            (
                "persons",
                ("person",),
                PersonsIndexTransformer,
                PersonsIndexDataLoader
            )
        )

        for index_name, table_names, transformer_class, pgloader_class in \
                scan_data:
            last_scan_date: str = state.get_state(
                f'{index_name}:last_scan_date',
            )
            if not last_scan_date:
                from_modified = datetime.datetime.min
            else:
                from_modified = datetime.datetime.fromisoformat(last_scan_date)

            es_uploader = ElasticUploader(
                es_manager,
                state,
                table_names=table_names,
                index_name=index_name,
                index_schema=load_es_mapping(
                    settings.elasticsearch_schema_path,
                    f'{index_name}.json'
                )
            )
            pgloader = pgloader_class(
                db=db,
                state=state,
                table_names=table_names,
            )
            while True:
                dirty_chunk = pgloader.load_data(
                    from_modified,
                    limit=chunk_size,
                )
                if not dirty_chunk:
                    logger.info(
                        "No more updates found to process."
                    )
                    break
                logger.info(
                    "Found %s records to work, start transformation.",
                    len(dirty_chunk)
                )
                clear_chunk = transformer_class().transform(dirty_chunk)
                logger.info(
                    "Push %s records to Elasticsearch to update index.",
                    len(clear_chunk)
                )
                es_uploader.bulk_upload(clear_chunk)

            self.update_last_scan_date(state, index_name, table_names)
            logger.info("Tables scan complete.")

    def update_last_scan_date(
        self,
        state: State,
        index_name: str,
        table_names: tuple[str, ...],
    ) -> None:
        """
        Update keys involved to keep state of scan.

        :param state: State Instance to manage persistent storage.
        :param index_name: Index name
        :param table_names: tuple[str, ...] Tuple of table names to manage
         state
        :return: None
        """
        state.set_state(
            f'{index_name}:last_scan_date',
            datetime.datetime.utcnow().isoformat(),
        )
        for table_name in table_names:
            state.set_state(
                f'{index_name}:{table_name}:already_processed_ids', []
            )
            state.set_state(
                f'{index_name}:{table_name}:current_iteration_selected_ids', []
            )

    def start(self) -> None:
        """Entry point of ETL application."""
        try:
            logger.info("ETL process started. To interrupt press Ctrl+C.")
            state_storage = JsonFileStorage('state.json')
            state = State(state_storage)
            db = DbManager(pg_dsn)
            es_manager = ElasticManager(settings.elasticsearch_url)
            while True:
                self.scan_tables(
                    db=db,
                    state=state,
                    es_manager=es_manager,
                    chunk_size=settings.limit
                )
                logger.info(
                    "Sleep for %s seconds, waiting for next scan cycle.",
                    settings.scan_delay
                )
                time.sleep(settings.scan_delay)
        except KeyboardInterrupt:
            logger.info("ETL process was interrupted by Ctrl+C.")
        finally:
            db.close()


if __name__ == '__main__':
    etl = ETL()
    etl.start()
