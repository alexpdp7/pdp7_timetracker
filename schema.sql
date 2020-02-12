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

create view reporting_activities_self_and_descendants as
    with recursive reporting_activities_self_and_descendants(id, descendant_id) as (
        select id, id as descendant_id
        from   activities
        union all
        select reporting_activities_self_and_descendants.id as id, activities.id as descendant_id
        from   reporting_activities_self_and_descendants
        join   activities on reporting_activities_self_and_descendants.descendant_id = activities.parent_id
    )
    select *
    from   reporting_activities_self_and_descendants;

create table tracked_periods (
    period                   tstzrange,
    activity_id              text not null references activities(id)
);

create function reporting_day_periods (now timestamp with time zone)
returns table(day date, period tstzrange) as $$
    select day::date, tstzrange(day, least(day + '1 day', now), '[)') as period
    from generate_series(
        (select date_trunc('day', min(lower(period)))
         from tracked_periods),
        (select date_trunc('day', max(coalesce(upper(period), lower(period))))
         from tracked_periods),
        '1 day') as days(day)
$$ language sql;

create function reporting_daily_tracked_periods (now timestamp with time zone)
returns table(activity_id text, day date, period tstzrange, length interval) as $$
    select tracked_periods.activity_id,
           reporting_day_periods.day,
           tracked_periods.period * reporting_day_periods.period as period,
           coalesce(upper(tracked_periods.period * reporting_day_periods.period),
                    lower(tracked_periods.period * reporting_day_periods.period))
           - lower(tracked_periods.period * reporting_day_periods.period) as length
    from   reporting_day_periods(now)
    join   tracked_periods on tracked_periods.period && reporting_day_periods.period
$$ language sql;

create function reporting_daily_tracked_periods_self_and_descendants (now timestamp with time zone)
returns table(id_path text, day date, period tstzrange, length interval) as $$
    select distinct reporting_activities.id_path,
           reporting_daily_tracked_periods.day,
           reporting_daily_tracked_periods.period,
           reporting_daily_tracked_periods.length
    from   reporting_daily_tracked_periods(now)
    join   reporting_activities_self_and_descendants on reporting_daily_tracked_periods.activity_id = reporting_activities_self_and_descendants.descendant_id
    join   reporting_activities on reporting_activities_self_and_descendants.id = reporting_activities.id
$$ language sql;
