from typing import TypeVar

from models.base_models import Base


class Genre(Base):
    """Response Genre model"""

    name: str


class Person(Base):
    """Response Person model"""

    full_name: str


class FilmInfoResponse(Base):
    """Full film info response."""

    title: str
    description: str
    imdb_rating: float
    genre: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]


class FilmSearchResponse(Base):
    """Film model for search response."""

    title: str
    imdb_rating: float


class PersonSearchResponse(Person):
    """Person model for search response."""

    role: str
    film_ids: list[str]


# Custom type for typing
ModelResponseType = TypeVar(
    'ModelResponseType',
    FilmInfoResponse,
    FilmSearchResponse,
    PersonSearchResponse,
)
