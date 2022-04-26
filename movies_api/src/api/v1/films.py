from fastapi import APIRouter, Depends, Request

from core.config import VIEW_CACHE_EXPIRE_IN_SECONDS
from api.v1.messages import FilmErrorMessage
from api.v1.utils import (
    CommonQueryParams,
    FilmQueryParams,
    FilterQueryParams,
    PaginateQueryParams,
    raise_http_404,
)
from models.data_models import Film
from models.response_models import FilmInfoResponse, FilmSearchResponse
from services.cache import cache
from services.films import FilmService, get_film_service


router = APIRouter()


@router.get('', response_model=list[FilmSearchResponse])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=FilmSearchResponse,
    serialize_collection=True,
)
async def films_popular(
        request: Request,  # required for cache decorator internal
        filter_params: FilterQueryParams = Depends(),
        paginate_params: PaginateQueryParams = Depends(),
        film_service: FilmService = Depends(get_film_service),
) -> list[FilmSearchResponse]:
    """
    Get popular filmworks by genre or just sorts them if a genre filter
    is not specified:

    - **page[number]**: The number of the displayed page
    - **page[size]**: The size of the data per page
    - **filter[genre]**: Filter by genre
    - **sort**: Field name to use in sort. (-imdb_rating means desc order)

    Example:
    - /api/v1/films?sort=-imdb_rating&page[number]=&lt;int&gt;&page[size]=&lt;int&gt;
    - /api/v1/films?filter[genre]=&lt;genre_uuid&gt;&sort=imdb_rating&page[number]=&lt;int&gt;&page[size]=&lt;int&gt;

    """
    films = await film_service.get_filtered_sort_films(
        filter_params,
        paginate_params
    )
    if not films:
        raise_http_404(FilmErrorMessage.not_found_popular_films)
    return [FilmSearchResponse(**film.dict()) for film in films]


@router.get('/search', response_model=list[FilmSearchResponse])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=FilmSearchResponse,
    serialize_collection=True,
)
async def film_search_by_text(
        request: Request,
        query_params: CommonQueryParams = Depends(),
        paginate_params: PaginateQueryParams = Depends(),
        film_service: FilmService = Depends(get_film_service),
) -> list[FilmSearchResponse]:
    """
    Get filmworks by the search word:

    - **query**: Word to search by.
    - **page[number]**: The number of the displayed page
    - **page[size]**: The size of the data per page

    Example:

    - /api/v1/films/search?query=&lt;str&gt;&page[number]=&lt;int&gt;&page[size]=&lt;int&gt;
    """

    films = await film_service.get_films_by_query(query_params, paginate_params)
    if not films:
        raise_http_404(FilmErrorMessage.not_found_current_query)
    return [FilmSearchResponse(**film.dict()) for film in films]


@router.get('/{film_id}', response_model=FilmInfoResponse)
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=FilmInfoResponse,
)
async def film_details_by_uuid(
        request: Request,
        film_params: FilmQueryParams = Depends(),
        film_service: FilmService = Depends(get_film_service),
) -> FilmInfoResponse:
    """
    Get full info about concrete filmwork by uuid:

    - **film_id**: Filmwork uuid

    Example:

    - /api/v1/films/&lt;film_id:uuid&gt;/
    """

    film = await film_service.get_film_by_id(film_params)
    if not film:
        raise_http_404(FilmErrorMessage.not_found_film_work_by_id)

    return FilmInfoResponse(**film.dict())


@router.get('/{film_id}/similar', response_model=list[FilmSearchResponse])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=FilmSearchResponse,
    serialize_collection=True,
)
async def films_similar(
        request: Request,
        film_params: FilmQueryParams = Depends(),
        film_service: FilmService = Depends(get_film_service)
) -> list[FilmSearchResponse]:
    """
    Get similar filmworks based on the current one:

    - **film_id**: Filmwork uuid

    Example:

    - /api/v1/films/&lt;film_id:uuid&gt;/similar
    """

    film = await film_service.get_document_by_id(
        film_params.film_id,
        Film,
        film_service.elastic_index
    )
    genres = [g.name for g in film.genre]
    films = await film_service.get_similar_films(genres)
    if not films:
        raise_http_404(FilmErrorMessage.not_found_similar_film)

    return [FilmSearchResponse(**film.dict()) for film in films]
