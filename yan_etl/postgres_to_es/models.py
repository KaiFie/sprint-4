from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel


class PersonRow(BaseModel):
    uuid: UUID
    full_name: str


class GenreRow(BaseModel):
    uuid: UUID
    name: str


class FilmWorkIndex(BaseModel):
    uuid: UUID
    imdb_rating: Optional[float]
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


class FilmWorkRow(BaseModel):
    uuid: UUID
    title: str


class GenreIndex(BaseModel):
    uuid: UUID
    name: str
    description: Optional[str]
    film_titles: str
    film_ids: List[FilmWorkRow]


class PersonIndex(BaseModel):
    uuid: UUID
    full_name: str
    role: List[str]
    film_titles: str
    film_ids: List[FilmWorkRow]
