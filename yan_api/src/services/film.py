from functools import lru_cache
from typing import Dict, Optional
from uuid import UUID

from aioredis import Redis
from elasticsearch import AsyncElasticsearch
from fastapi import Depends

from api.v1.schemas import FilmItem as ApiFilmItem
from core.config import FILM_CACHE_EXPIRE_IN_SECONDS
from db.elastic import get_elastic
from db.redis import get_redis
from models.film import FilmItem, FilmList


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_uuid: UUID) -> Optional[ApiFilmItem]:
        film = await self._film_from_cache(film_uuid)
        if not film:
            film = await self._get_film_from_elastic(film_uuid)
            if not film:
                return None

            await self._put_film_to_cache(film)

        return ApiFilmItem(**film.dict(include={i for i in ApiFilmItem.__fields__}))

    async def _get_film_from_elastic(self, film_uuid: UUID) -> Optional[FilmItem]:

        doc = await self.elastic.get('movies', film_uuid)
        return FilmItem(**doc['_source'])

    async def _film_from_cache(self, film_uuid: UUID) -> Optional[FilmItem]:

        data = await self.redis.get('film_' + str(film_uuid))
        if not data:
            return None

        film = FilmItem.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: FilmItem):

        await self.redis.set('film_' + str(film.uuid), film.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def get_list(self, page: int = 1, size: int = 50,
                       sorting: Dict = {'imdb_rating': 'desc'}, genre: Optional[UUID] = None,
                       person: Optional[UUID] = None, query: Optional[str] = None) -> Optional[FilmList]:

        cache_key = 'film_list_page={}_size={}_sort={}'.format(page, size, str(sorting))
        if genre is not None:
            cache_key = cache_key + '_genre=' + str(genre)
        if query is not None:
            cache_key = cache_key + '_query=' + str(query)
        if person is not None:
            cache_key = cache_key + 'person=' + str(person)

        films = await self._film_list_from_cache(cache_key)
        if not films:
            films = await self._get_films_from_elastic(page=page, size=size, sorting=sorting, genre=genre, query=query,
                                                       person=person)
            if not films:
                return None
            await self._put_film_list_to_cache(cache_key, films)

        return films

    async def _film_list_from_cache(self, cache_key: str) -> Optional[FilmList]:

        data = await self.redis.get(cache_key)
        if not data:
            return None

        films = FilmList.parse_raw(data)
        return films

    async def _put_film_list_to_cache(self, cache_key: str, films: FilmList):

        await self.redis.set(cache_key, films.json(), expire=FILM_CACHE_EXPIRE_IN_SECONDS)

    async def _get_films_from_elastic(self, page: int, size: int, sorting: Dict,
                                      genre: Optional[UUID] = None, query: Optional[str] = None,
                                      person: Optional[UUID] = None) -> FilmList:

        body = {
            'from': page * size - size,
            'size': size,
            'sort': [
                sorting,
                '_score'
            ],
            'query': {
                'bool': {
                    'must': [

                    ]
                }
            }
        }

        if query is not None:
            query_item = {
                'match': {
                    'title': {
                        'query': query,
                        'operator': 'and',
                        'fuzziness': 'auto'
                    }
                }
            }
            body['query']['bool']['must'].append(query_item)

        if genre is not None:
            genre_item = {
                'nested': {
                    'path': 'genre',
                    'query': {
                        'bool': {
                            'must': [
                                {
                                    'match': {
                                        'genre.uuid': genre
                                    }
                                }
                            ]
                        }
                    }
                }
            }
            body['query']['bool']['must'].append(genre_item)

        if person is not None:

            person_item = {
                'bool': {
                    'should': []
                }
            }
            for table in ['actors', 'writers', 'directors']:
                person_item['bool']['should'].append(
                    {
                        'nested':
                            {
                                'path': table,
                                'query': {
                                    'bool': {
                                        'must': {
                                            'match': {table + '.uuid': person}
                                        }
                                    }
                                }
                            }
                    })
            body['query']['bool']['must'].append(person_item)

        doc = await self.elastic.search(index='movies', body=body)

        items = [FilmItem(**i['_source']) for i in doc['hits']['hits']]
        total = doc['hits']['total']['value']

        return FilmList(items=items, total=total)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)
