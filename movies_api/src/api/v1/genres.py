from fastapi import APIRouter, Depends, Request, Path

from api.v1.messages import GenreErrorMessage
from api.v1.utils import (
    PaginateQueryParams,
    raise_http_404
)
from core.config import VIEW_CACHE_EXPIRE_IN_SECONDS

from models.response_models import Genre
from services.cache import cache
from services.genres import GenreService, get_genre_service

router = APIRouter()


@router.get('', response_model=list[Genre])
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=Genre,
    serialize_collection=True,
)
async def get_genres(
    request: Request,
    paginate_params: PaginateQueryParams = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
) -> list[Genre]:
    """
    Get list of genres:

    - **page[number]**: The number of the displayed page
    - **page[size]**: The size of the data per page

    Example:
    - /api/v1/genres?page[number]=&lt;int&gt;&page[size]=&lt;int&gt;
    """

    genres = await genre_service.get_genres_list(paginate_params)
    if not genres:
        raise_http_404(GenreErrorMessage.not_found_genres)
    return [Genre(**genre.dict()) for genre in genres]


@router.get('/{genre_id}', response_model=Genre)
@cache(
    expire=VIEW_CACHE_EXPIRE_IN_SECONDS,
    serializer_class=Genre
)
async def genre_details_by_uuid(
    request: Request,
    genre_id: str = Path(
        ...,
        title='Genre uuid',
        description='Genre uuid.',
    ),
    genre_service: GenreService = Depends(get_genre_service),
) -> Genre:
    """
    Get full info about genre by uuid:

    - **genre_id**: Genre uuid

    Example:

    - /api/v1/genres/&lt;genre_id:uuid&gt;/
    """

    genre = await genre_service.get_genre_by_id(genre_id)
    if not genre:
        raise_http_404(GenreErrorMessage.not_found_genre)
    return Genre(**genre.dict())
