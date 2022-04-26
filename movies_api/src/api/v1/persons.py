from enum import Enum
from fastapi import APIRouter, Depends, Request, Query, Path

from core.config import VIEW_CACHE_EXPIRE_IN_SECONDS
from api.v1.messages import PersonErrorMessage
from api.v1.utils import (
    PaginateQueryParams,
    raise_http_404
)
from models.response_models import PersonSearchResponse, FilmSearchResponse
from services.cache import cache
from services.persons import PersonService, get_person_service

router = APIRouter()


class Role(Enum):
    actor = 'actor'
    director = 'director'
    writer = 'writer'


@router.get('/search', response_model=list[PersonSearchResponse])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=PersonSearchResponse,
    serialize_collection=True,
)
async def search_persons_by_name(
    request: Request,
    query: str = Query(
        None,
        title='Search by full name field.',
        description='Search and return persons whom full_name match query text'
    ),
    paginate_params: PaginateQueryParams = Depends(),
    person_service: PersonService = Depends(get_person_service),
) -> list[PersonSearchResponse]:
    """
    Get list of persons who name hast query text:
    - **query_text**: Text to use in search by full_name field.
    - **page[number]**: The number of the displayed page
    - **page[size]**: The size of the data per page

    Example:
    - /api/v1/persons/search?query=captain&page[number]=&lt;int&gt;&page[size]=&lt;int&gt;
    """

    persons = await person_service.get_persons_by_query(
        query,
        paginate_params
    )
    if not persons:
        raise_http_404(PersonErrorMessage.not_found_persons)
    return [PersonSearchResponse(**person.dict()) for person in persons]


@router.get('/{person_id}', response_model=list[PersonSearchResponse])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=PersonSearchResponse,
    serialize_collection=True
)
async def get_persons_by_uuid(
        request: Request,
        person_id: str = Path(
            ...,
            title='Person uuid',
            description='Person uuid.',
        ),
        person_service: PersonService = Depends(get_person_service),
) -> list[PersonSearchResponse] | None:
    """
    Get list of person info by uuid for every person's role:

    - **person_id**: Person uuid

    Example:

    - /api/v1/persons/&lt;person_id:uuid&gt;/
    """

    person_ids = [
        '{0}:{1}'.format(person_id, role.value) for role in (
            Role.actor, Role.writer, Role.director
        )
    ]
    persons = await person_service.get_persons_by_ids(person_ids)
    if not persons:
        raise_http_404(PersonErrorMessage.not_found_info_about_person)
    return [PersonSearchResponse(**person.dict()) for person in persons]


@router.get(
    '/{person_id}/films',
    response_model=list[FilmSearchResponse],
    deprecated=True,
)
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=FilmSearchResponse,
    serialize_collection=True
)
async def get_person_films(
    request: Request,
    person_id: str = Path(
        ...,
        title='Person uuid',
        description='Person uuid.',
    ),
    role: Role = Query(
        Role.actor,
        title='Role filter',
        description='Role filter values might be one of writer, actor,'
                    ' director. Default: filter[role]=actor',
        alias='filter[role]',
    ),
    person_service: PersonService = Depends(get_person_service),
) -> list[FilmSearchResponse]:
    """
    Get list of films which person related to as actor, director or writer.

    - **person_id**: Person uuid
    - **role**: Mandatory filter (actor|director|writer)

    Example:

    - /api/v1/persons/&lt;person_id:uuid&gt;/films?filter[role]=actor
    returns all films where person was an actor
    """

    person = await person_service.get_person_by_id(
        person_id + ':' + role.value
    )
    if not person:
        raise_http_404(
            f'Person not found by uuid: {person_id}'
            f' and role: {role.value}'
        )
    films = await person_service.get_person_films(
        film_ids=person.film_ids,
    )
    if not films:
        raise_http_404(PersonErrorMessage.not_found_films_for_person)
    return [FilmSearchResponse(**film.dict()) for film in films]
