with
    constant_created_at AS (VALUES (cast(%s as timestamp with time zone))),
    constant_limit AS (VALUES (%s)),
    person_for_update as (
        select distinct
            person.id,
            max(least(person.created_at, person_film_work.created_at)) as updated_at
        from
            person
                left join person_film_work
                    left join film_work
                        on person_film_work.film_work_id = film_work.id
                            and coalesce(film_work.created_at, '0001-01-01') > (table constant_created_at)
                    on person.id = person_film_work.person_id
                        and coalesce(person_film_work.created_at, '0001-01-01') > (table constant_created_at)
        where
            least(person.created_at, film_work.created_at) > (table constant_created_at)
        group by
            person.id
        order by
            max(least(person.created_at, person_film_work.created_at)),
            person.id
        limit (table constant_limit)),
    data_to_export as(
        select
            person.id as uuid,
            person.full_name as full_name,
            array_agg(distinct person_film_work.role order by person_film_work.role) as role,
            array_to_string(array_agg(distinct film_work.title order by film_work.title), ', ') as film_titles,
            jsonb_agg(distinct jsonb_strip_nulls(jsonb_build_object('uuid', film_work.id, 'title', film_work.title))) as film_ids
        from
            person_for_update
                inner join person
                    left join person_film_work
                        left join film_work
                            on person_film_work.film_work_id = film_work.id
                        on person.id = person_film_work.person_id
                    on person_for_update.id = person.id
        group by
            person.id,
            person.full_name,
            person_for_update.updated_at)
    select
        jsonb_agg(to_jsonb(data_to_export)),
        max(person_for_update.updated_at) as updated_at
    from
        data_to_export
            inner join person_for_update
                on data_to_export.uuid = person_for_update.id;
