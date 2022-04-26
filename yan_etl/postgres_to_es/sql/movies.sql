with
    constant_created_at AS (VALUES (cast(%s as timestamp with time zone))),
    constant_limit AS (VALUES (%s)),
    film_work_for_update as (
select distinct
    film_work.id,
    max(least(film_work.created_at, genre_film_work.created_at, genre.created_at, person_film_work.created_at, person.created_at)) as updated_at
from
    "content".film_work as film_work
        left join "content".genre_film_work as genre_film_work
            left join "content".genre as genre
                on genre_film_work.genre_id = genre.id
                    and coalesce(genre.created_at, '0001-01-01') > (table constant_created_at)
            on film_work.id = genre_film_work.film_work_id
                and coalesce(genre_film_work.created_at, '0001-01-01') > (table constant_created_at)
        left join "content".person_film_work as person_film_work
            left join "content".person as person
                on person_film_work.person_id = person.id
                    and coalesce(person.created_at, '0001-01-01') > (table constant_created_at)
            on film_work.id = person_film_work.film_work_id
                and coalesce(person_film_work.created_at, '0001-01-01') > (table constant_created_at)
where
    least(film_work.created_at, genre_film_work.created_at, genre.created_at, person_film_work.created_at, person.created_at) > (table constant_created_at)
group by
    film_work.id
order by
    max(least(film_work.created_at, genre_film_work.created_at, genre.created_at, person_film_work.created_at, person.created_at)),
    film_work.id
limit (table constant_limit)),
data_to_export as(
    select
        filmwork.id as uuid,
        filmwork.rating as imdb_rating,
        array_to_string(array_agg(distinct genre.name order by genre.name), ', ') as genres_names,
        jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', genre.id, 'name', genre.name))) as genre,
        filmwork.title as title,
        filmwork.description as description,
        case when length(array_to_string(array_agg(distinct directors.full_name order by directors.full_name), ', ')) > 0 then array_to_string(array_agg(distinct directors.full_name order by directors.full_name), ', ')  else null end as director,
        case when length(array_to_string(array_agg(distinct actors.full_name order by actors.full_name), ', ')) > 0 then array_to_string(array_agg(distinct actors.full_name order by actors.full_name), ', ') else null end as actors_names,
        case when length(array_to_string(array_agg(distinct writers.full_name order by writers.full_name), ', ')) > 0 then array_to_string(array_agg(distinct writers.full_name order by writers.full_name), ', ') else null end as writers_names,
        case
            when jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', directors.id, 'full_name', directors.full_name))) = '[{}]'
            then '[]'
            else jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', directors.id, 'full_name', directors.full_name)))
        end as directors,
        case
            when jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', actors.id, 'full_name', actors.full_name))) = '[{}]'
            then '[]'
            else jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', actors.id, 'full_name', actors.full_name)))
        end as actors,
        case
            when jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', writers.id, 'full_name', writers.full_name))) = '[{}]'
            then '[]'
            else jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', writers.id, 'full_name', writers.full_name)))
        end as writers
    from
        film_work_for_update as film_work_for_update
            inner join content.film_work as filmwork
                left join content.genre_film_work as genre_film_work
                    left join content.genre as genre
                        on genre_film_work.genre_id = genre.id
                    on filmwork.id = genre_film_work.film_work_id
                left join content.person_film_work as directors_link
                    left join content.person as directors
                        on directors_link.person_id = directors.id
                    on filmwork.id = directors_link.film_work_id
                        and directors_link.role = 'director'
                left join content.person_film_work as actors_link
                    left join content.person as actors
                        on actors_link.person_id = actors.id
                    on filmwork.id = actors_link.film_work_id
                        and actors_link.role = 'actor'
                left join content.person_film_work as writers_link
                    left join content.person as writers
                        on writers_link.person_id = writers.id
                    on filmwork.id = writers_link.film_work_id
                        and writers_link.role = 'writer'
                on film_work_for_update.id = filmwork.id
    group by
        filmwork.id,
        filmwork.rating,
        filmwork.title,
        filmwork.description,
        film_work_for_update.updated_at)
select
    jsonb_agg(to_jsonb(data_to_export)),
    max(film_work_for_update.updated_at) as updated_at
from
    data_to_export as data_to_export
        inner join film_work_for_update as film_work_for_update
            on data_to_export.uuid = film_work_for_update.id;
