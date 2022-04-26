"""
API по персонам.
Возвращает персону, его роли, и список фильмов с его участием.
"""
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_pagination import Page, Params

from services.person import PersonService, get_person_service
from services.film import FilmService, get_film_service


from .schemas import APIFilmRow, APIPersonItem, FilmRow

router = APIRouter()


@router.get('/search', response_model=Page[APIPersonItem], summary='Search persons')
async def persons_search(
        query: str,
        size: int = Query(50, alias='page[size]'),
        page: int = Query(1, alias='page[number]'),
        person_service: PersonService = Depends(get_person_service)
) -> Page[APIPersonItem]:
    """
    Функция возвращает список персон соответствующих GET запросу
    При отсутствии совпадений вызывает исключение.
    """
    persons = await person_service.get_list(page=page, size=size, query=query)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')

    return Page[APIPersonItem].create(items=persons.items, total=persons.total, params=Params(page=page, size=size))

@router.get('/{person_id}/film/', response_model=Page[FilmRow])
async def person_film(person_id: UUID, size: int = Query(50, alias='page[size]'),
                      page: int = Query(1, alias='page[number]'),
                      film_service: FilmService = Depends(get_film_service)) -> Page[FilmRow]:
    """
    Функция возвращает по ID спискок фильмов.
    """
    films = await film_service.get_list(page=page, size=size, person=person_id)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')

    return Page[FilmRow].create(items=films.items, total=films.total, params=Params(page=page, size=size))

@router.get('/{person_id}/', response_model=APIPersonItem)
async def person_detail(person_id: UUID, person_service: PersonService = Depends(get_person_service)) -> APIPersonItem:
    """
    Функция возвращает по ID персону со списком фильмов и ролями.
    При отсутствии ID вызывает исключение.
    """
    person = await person_service.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    film_ids = [APIFilmRow(uuid=film.uuid, title=film.title) for film in person.film_ids]
    return APIPersonItem(uuid=person.uuid, full_name=person.full_name, role=person.role, film_ids=film_ids)
