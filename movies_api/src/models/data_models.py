from typing import TypeVar
from enum import Enum

from models.base_models import Base


class Genre(Base):
    """Representation of docs from genres index."""

    name: str


class Person(Base):
    """Representation of nested structure of person's
    related data into Film model."""

    full_name: str


class PersonExt(Person):
    """Representation of document in persons index into Elasticsearch."""

    role: str
    film_ids: list[str]


class Film(Base):
    """Representation of document in movies index into Elasticsearch."""

    imdb_rating: float = None
    genre: list[Genre] = []
    title: str
    description: str = None
    directors: list[Person] = []
    actors_names: list[str] = []
    writers_names: list[str] = []
    actors: list[Person] = []
    writers: list[Person] = []


class FilmShort(Base):
    """Short representation of document in movies index into Elasticsearch"""

    title: str
    imdb_rating: float = None


# Type that represents data from Elasticsearch.
ModelType = TypeVar('ModelType', Film, Genre, Person, PersonExt, FilmShort)


class Tags(Enum):
    """Enum to use for declare API collections tags attribute."""

    filmworks = 'films'
    persons = 'persons'
    genres = 'genres'
