from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from services.genre import GenreService, get_genre_service

from .schemas import APIFilmRow, APIGenreItem, APIGenreList, APIGenreListRow

router = APIRouter()


@router.get('/', response_model=APIGenreList)
async def genre_list(size: int = Query(50, alias='page[size]'),
                     genre_service: GenreService = Depends(get_genre_service)) -> APIGenreList:
    genres, count = await genre_service.get_list_genre(size)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genres not found')
    items = [APIGenreListRow(uuid=genre.uuid, name=genre.name) for genre in genres]
    return APIGenreList(items=items, count=count)


@router.get('/{genre_id}', response_model=APIGenreItem)
async def genre_detail(genre_id: UUID, genre_service: GenreService = Depends(get_genre_service)) -> APIGenreItem:
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    film_ids = [APIFilmRow(uuid=film.uuid, title=film.title) for film in genre.film_ids]
    return APIGenreItem(uuid=genre.uuid, name=genre.name, description=genre.description, film_ids=film_ids)
