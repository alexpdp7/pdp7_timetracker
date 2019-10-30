create schema if not exists pdp7_timetracker;

set search_path to pdp7_timetracker;

create table activities (
    id                       text primary key,
    parent_id                text null references activities(id)
);

create view reporting_activities as
    with recursive hierarchical_activities(id, parent_id, id_path) as (
        select id, parent_id, id as id_path
        from   activities
        where  parent_id is null
        union all
        select activities.id, activities.parent_id, hierarchical_activities.id_path || ' / ' || activities.id
        from   activities
        join   hierarchical_activities on hierarchical_activities.id = activities.parent_id
    )
    select *
    from   hierarchical_activities;

create table tracked_period (
    period                   tstzrange,
    activity_id              text not null references activities(id)
);
