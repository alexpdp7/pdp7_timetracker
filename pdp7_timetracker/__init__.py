import datetime

import psycopg2.extras


__version__ = "0.1.0"


class TimeTracker:
    def activities(self, *, sql):
        return sql.query("select * from reporting_activities order by id_path")

    def new_activity(self, *args, sql):
        parent = None
        for arg in args:
            sql.dml(
                "insert into activities(id, parent_id) values (%(id)s, %(parent_id)s) on conflict do nothing",
                id=arg,
                parent_id=parent,
            )
            parent = arg

    def new_tracked_period(self, activity, lower, upper, *, sql):
        sql.dml(
            "insert into tracked_periods(period, activity_id) values (%(range)s, %(activity_id)s)",
            activity_id=activity,
            range=psycopg2.extras.DateTimeTZRange(lower=lower, upper=upper),
        )

    def stop(self, *, sql, now):
        sql.dml(
            "update tracked_periods set period = tstzrange(lower(period), %(upper)s) where upper(period) is null",
            upper=now,
        )

    def start(self, *activities, sql, now):
        self.stop(sql=sql, now=now)
        for activity in activities:
            self.new_tracked_period(activity, now, None, sql=sql)

    def get_schema(self):
        with open("schema.sql") as s:
            return s.read()

    def load_schema(self, *, sql):
        sql.ddl(self.get_schema())

    def daily_report(self, day=None, *, sql, now):
        day = day or datetime.date.today()
        return sql.query(
            "select id_path, sum(length) as total from reporting_daily_tracked_periods_self_and_descendants(%(now)s) where day = %(day)s group by id_path order by sum(length) desc",
            day=day,
            now=now,
        )
