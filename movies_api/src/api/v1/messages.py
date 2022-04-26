from enum import Enum


class FilmErrorMessage(Enum):
    not_found_popular_films = 'Popular films not found'
    not_found_current_query = 'Not found for the current query'
    not_found_film_work_by_id = 'Filmwork with this ID not found'
    not_found_similar_film = 'Similar films not found'


class GenreErrorMessage(Enum):
    not_found_genres = 'Genres are not found'
    not_found_genre = 'Genre was not found'


class PersonErrorMessage(Enum):
    not_found_persons = 'Persons not found'
    not_found_info_about_person = 'Info about person not found'
    not_found_films_for_person = 'Films for person not found'
