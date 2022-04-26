from pydantic import BaseModel, Field


class Genre(BaseModel):
    """Genre entity representation model as part of MoviesIndexRecord.."""

    uuid: str
    name: str


class Person(BaseModel):
    """Person entity representation model as part of MoviesIndexRecord."""

    uuid: str
    full_name: str = Field(alias='name')


class MoviesIndexRecord(BaseModel):
    """Class represents record that satisfy 'movies' index document schema."""

    uuid: str = Field(alias='id')
    title: str
    description: str = None
    directors: list[Person] = []
    genre: list[Genre] = []
    imdb_rating: float = None
    actors: list[Person] = []
    actors_names: list[str] = []
    writers: list[Person] = []
    writers_names: list[str] = []


class PersonsIndexRecord(BaseModel):
    """Class represents record that satisfy 'persons' index document schema."""

    uuid: str
    full_name: str
    role: str
    film_ids: list[str] = []


class GenresIndexRecord(Genre):
    """Class represents record that satisfy 'genres' index document schema."""

    uuid: str = Field(alias='id')
