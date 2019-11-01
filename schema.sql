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

create table tracked_period (
    period                   tstzrange,
    activity_id              text not null references activities(id)
);

create view reporting_day_periods as (
    select day::date, tstzrange(day, day + '1 day', '[)') as period
    from generate_series(
        (select date_trunc('day', min(lower(period)))
         from tracked_period),
        (select date_trunc('day', max(coalesce(upper(period), lower(period))))
         from tracked_period),
        '1 day') as days(day));

create view reporting_daily_tracked_periods as (
    select tracked_period.activity_id,
           reporting_day_periods.day,
           tracked_period.period * reporting_day_periods.period as period,
           coalesce(upper(tracked_period.period * reporting_day_periods.period),
                    lower(tracked_period.period * reporting_day_periods.period))
           - lower(tracked_period.period * reporting_day_periods.period) as length
    from   reporting_day_periods
    join   tracked_period on tracked_period.period && reporting_day_periods.period
);

create view reporting_daily_tracked_periods_self_and_descendants as (
    select reporting_activities.id_path,
           reporting_daily_tracked_periods.day,
           reporting_daily_tracked_periods.period,
           reporting_daily_tracked_periods.length
    from   reporting_daily_tracked_periods
    join   reporting_activities_self_and_descendants on reporting_daily_tracked_periods.activity_id = reporting_activities_self_and_descendants.descendant_id
    join   reporting_activities on reporting_activities_self_and_descendants.id = reporting_activities.id
);
