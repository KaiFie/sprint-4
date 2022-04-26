from enum import Enum
from http import HTTPStatus
from fastapi import HTTPException, Path, Query


def raise_http_404(exception_text: str | Enum = 'Not found.'):
    """Shortcut to raise HTTPStatus.NOT_FOUND with text details."""

    raise HTTPException(
        status_code=HTTPStatus.NOT_FOUND,
        detail=exception_text if not isinstance(
            exception_text, Enum) else exception_text.value)


class CommonQueryParams:
    """Dependency class to parse text query param."""

    def __init__(
        self,
        query: str = Query(
            ...,
            title='Query string.',
            description='Search by text word.'
        ),
    ):
        self.query = query

    def __repr__(self):
        return 'query={query}'.format(
            query=self.query or ''
        )


class PaginateQueryParams:
    """Dependency class to parse pagination query params."""

    def __init__(
        self,
        page_number: int = Query(
            1,
            title='Page number.',
            description='Page number to return',
            alias='page[number]',
            ge=1,
        ),
        page_size: int = Query(
            50,
            title='Size of page.',
            description='The number of records returned per page',
            alias='page[size]',
            ge=1,
            le=500,
        ),
    ):
        self.page_number = page_number
        self.page_size = page_size

    def __repr__(self):
        return 'page_number={page_number},page_size={page_size}'.format(
            page_number=self.page_number,
            page_size=self.page_size
        )


class FilterQueryParams:
    """Dependency class to parse filmwork filter and sort query params."""

    def __init__(
        self,
        filter_genre: str = Query(
            None,
            title='Filter by genre.',
            description='Search and return all filmworks those belong to that '
                        'genre uuid',
            alias='filter[genre]'
        ),
        sort: str | None = Query(
            '-imdb_rating',
            title='Sort field',
            description='The field by which the sorting takes place',
        ),
    ):
        self.filter_genre: str = filter_genre
        self.sort = sort

    def __repr__(self):
        return 'sort={sort},filter[genre]={filter}'.format(
            sort=self.sort,
            filter=self.filter_genre or ''
        )


class FilmQueryParams:
    """Dependency class to parse filmwork uuid query param."""

    def __init__(
        self,
        film_id: str = Path(
            ...,
            title='Filmwork uuid',
            description='Filmworks uuid.',
        ),
    ):
        self.film_id: str = film_id

    def __repr__(self):
        return 'film_id={film_id}'.format(
            film_id=self.film_id
        )
