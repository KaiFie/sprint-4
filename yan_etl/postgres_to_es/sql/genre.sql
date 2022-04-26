with
    constant_created_at AS (VALUES (cast(%s as timestamp with time zone))),
    constant_limit AS (VALUES (%s)),
    genre_for_update as (
        select distinct
            genre.id,
            max(least(genre.created_at, genre_film_work.created_at)) as updated_at
        from
            genre
                left join genre_film_work
                    left join film_work
                        on genre_film_work.film_work_id = film_work.id
                            and coalesce(film_work.created_at, '0001-01-01') > (table constant_created_at)
                    on genre.id = genre_film_work.genre_id
                        and coalesce(genre_film_work.created_at, '0001-01-01') > (table constant_created_at)
        where
            least(genre.created_at, film_work.created_at) > (table constant_created_at)
        group by
            genre.id
        order by
            max(least(genre.created_at, genre_film_work.created_at)),
            genre.id
        limit (table constant_limit)),
    data_to_export as(
        select
            genre.id as uuid,
            genre.name as name,
            genre.description as description,
            array_to_string(array_agg(distinct film_work.title order by film_work.title), ', ') as film_titles,
            jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', film_work.id, 'title', film_work.title))) as film_ids
        from
            genre_for_update
                inner join genre
                    left join genre_film_work
                        left join film_work
                            on genre_film_work.film_work_id = film_work.id
                        on genre.id = genre_film_work.genre_id
                    on genre_for_update.id = genre.id
        group by
            genre.id,
            genre.name,
            genre.description,
            genre_for_update.updated_at)
    select
        jsonb_agg(to_jsonb(data_to_export)),
        max(genre_for_update.updated_at) as updated_at
    from
        data_to_export
            inner join genre_for_update
                on data_to_export.uuid = genre_for_update.id;
