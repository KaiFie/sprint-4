import logging
from typing import List, Union

from models import FilmWorkIndex, GenreIndex

logger = logging.getLogger()


class Transform:
    """
    The class implements transform data to load in Elasticsearch database
    """
    def __init__(self, data: List[Union[FilmWorkIndex, GenreIndex]], index_name: str):
        self.data = data
        self.index_name = index_name

    def get_data(self) -> List[dict]:
        """ The method returns a generator with prepared data """
        actions = []
        for item in self.data:
            action = {
                "_index": self.index_name,
                "_id": item.uuid,
                "_source": item.dict()
            }
            actions.append(action)
        return actions
