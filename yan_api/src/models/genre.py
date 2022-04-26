from typing import List, Optional

from .base import Base


class FilmRow(Base):
    title: str


class GenreItem(Base):
    name: str
    description: Optional[str]
    film_titles: str
    film_ids: List[FilmRow]
