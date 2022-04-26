from typing import List, Optional, Union
from uuid import UUID

from pydantic import BaseModel


class PersonRow(BaseModel):
    uuid: UUID
    full_name: str


class GenreRow(BaseModel):
    uuid: UUID
    name: str


class FilmRow(BaseModel):
    uuid: UUID
    title: str
    imdb_rating: float


class FilmItem(BaseModel):
    uuid: UUID
    imdb_rating: float
    genres_names: str
    genre: List[GenreRow]
    title: str
    description: Optional[str]
    actors: List[PersonRow]
    writers: List[PersonRow]
    directors: List[PersonRow]


class APIFilmRow(BaseModel):
    uuid: UUID
    title: str


class APIGenreItem(BaseModel):
    uuid: UUID
    name: str
    description: Optional[str]
    film_ids: List[APIFilmRow]


class APIGenreListRow(BaseModel):
    uuid: UUID
    name: str


class APIGenreList(BaseModel):
    items: List[APIGenreListRow]
    count: int


class APIPersonItem(BaseModel):
    uuid: UUID
    full_name: str
    role: Union[list, str]
    film_ids: List[APIFilmRow]
