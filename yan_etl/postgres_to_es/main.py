import datetime
import json
import logging
from time import sleep

from config import config
from extract import Extract
from load import Load
from state import State
from transform import Transform

logger = logging.getLogger('ETL')
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler()
ch.setLevel(config.LOGGER_LEVEL)
ch.setFormatter(formatter)
logger.addHandler(ch)


pg_dsl = {
    "database": config.PG_DBNAME,
    "user": config.PG_USER,
    "password": config.PG_PASSWORD.get_secret_value(),
    "host": config.PG_HOST,
    "port": config.PG_PORT,
    "options": "-c search_path={}".format(config.PG_SCHEMA)
}

el_dsl = {'host': config.ES_HOST, "port": config.ES_PORT}


def get_indices() -> dict:
    """
    Load from json file indices
    """
    with open(config.INDICES_FILE_PATH, "r") as file:
        return json.load(file)


def create_indices(es_load, indices: dict):
    """
    This method create index to elasticsearch database if index is not exist
    """
    for index in indices.keys():
        if not es_load.cat_index(index):
            logger.info(f"Index {index} not found!")
            es_load.crate_index(index, indices[index])
            logger.info(f"Index {index} create successful.")


def main():
    extract = Extract(pg_dsl, config.LIMIT)
    es_load = Load(el_dsl)
    
    state = State(config.STATE_FILE_PATH)

    indices = get_indices()
    create_indices(es_load, indices)

    while True:
        logger.info(f"Start extract data from Postgres server with limit {config.LIMIT}.")
        for index_name in indices.keys():
            updated_at = state.get_state(f"{index_name}_update_at", datetime.datetime(1, 1, 1, tzinfo=datetime.timezone.utc))
            data, updated_at = extract.fetch_data(updated_at, config.LIMIT, index_name)
            logger.info("Extract data from index {} end. Total length {}.".format(index_name, len(data)))
            if len(data) == 0:
                sleep(config.BULK_TIMER)
                continue
            logger.info(f"Start transform data.")
            transform = Transform(data, index_name)
            data = transform.get_data()
            logger.info("Transform data successful end.")

            logger.info(f"Start load data to Elasticsearch")
            info = es_load.load_data(data)
            if updated_at is not None:
                state.set_state(f"{index_name}_update_at", updated_at)

            logger.info(info)
            logger.info(f"Load data successful.")

        sleep(config.BULK_TIMER)


if __name__ == '__main__':
    main()
