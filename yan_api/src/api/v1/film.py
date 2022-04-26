from enum import Enum
from http import HTTPStatus
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page, Params

from services.film import FilmService, get_film_service

from .schemas import FilmItem, FilmRow

router = APIRouter()


class Sorting(str, Enum):
    imdb_rating_desc = '-imdb_rating'
    imdb_rating_asc = 'imdb_rating'

    def get_sorting(self) -> dict:
        if self == Sorting.imdb_rating_asc:
            return {"imdb_rating": "asc"}

        # default sorting
        return {"imdb_rating": "desc"}


@router.get('/search/', response_model=Page[FilmRow], summary='Search movies')
async def films_search(query: str,
                       size: int = Query(50, alias='page[size]'),
                       page: int = Query(1, alias='page[number]'),
                       film_service: FilmService = Depends(get_film_service)) -> Page[FilmRow]:
    """
    Movie search based on text query:

    - **query**: text query
    - **size**: sample size
    - **page**: sample page
    """

    films = await film_service.get_list(page=page, size=size, query=query)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return Page[FilmRow].create(items=films.items, total=films.total, params=Params(page=page, size=size))


@router.get('/{film_uuid}/', response_model=FilmItem, summary='Getting information about a movie')
async def film_details(film_uuid: UUID, film_service: FilmService = Depends(get_film_service)) -> FilmItem:
    """
    Getting information about a movie.

    - **film_uuid**: movie uuid
    """
    film = await film_service.get_by_id(film_uuid)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')

    return film


@router.get('/', response_model=Page[FilmRow], summary='Getting a list of movies')
async def film_list(sort: Sorting = Sorting.imdb_rating_desc,
                    genre: Optional[UUID] = Query(None, alias='filter[genre]'),
                    size: int = Query(50, alias='page[size]'),
                    page: int = Query(1, alias='page[number]'),
                    film_service: FilmService = Depends(get_film_service)) -> Page[FilmRow]:
    """
    Getting a list of movies:

    - **genre**: genre uuid if you want to filter by genre
    - **size**: sample size
    - **page**: sample page
    """
    films = await film_service.get_list(page=page, size=size, sorting=sort.get_sorting(), genre=genre)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return Page[FilmRow].create(items=films.items, total=films.total, params=Params(page=page, size=size))
