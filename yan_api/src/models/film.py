from typing import List, Optional

from pydantic import BaseModel

from .base import Base


class PersonRow(Base):
    full_name: str


class GenreRow(Base):
    name: str


class FilmItem(Base):
    imdb_rating: float
    genres_names: str
    genre: List[GenreRow]
    title: str
    description: Optional[str]
    director: Optional[str]
    actors_names: Optional[str]
    writers_names: Optional[str]
    actors: List[PersonRow]
    writers: List[PersonRow]
    directors: List[PersonRow]


class FilmList(BaseModel):
    items: List[FilmItem]
    total: int
