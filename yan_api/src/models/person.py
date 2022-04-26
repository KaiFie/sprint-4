"""
Pydantic модель персоны.
"""
from typing import List, Union

from pydantic import BaseModel

from .base import Base


class FilmRow(Base):
    """
    Pydantic класс с фильмом
    """
    title: str


class PersonItem(Base):
    """
    Pydantic класс с данными по персоне
    """
    full_name: str
    role: Union[list, str]
    film_titles: str
    film_ids: List[FilmRow]


class PersonList(BaseModel):
    """
    Pydantic класс списка персон
    """
    items: List[PersonItem]
    total: int
