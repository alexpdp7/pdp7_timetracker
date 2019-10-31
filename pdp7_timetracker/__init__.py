import configparser
import datetime
import pathlib

import appdirs
import psycopg2
import psycopg2.extras


__version__ = "0.1.0"


def config_dir():
    return appdirs.user_config_dir("pdp7_timetracking")


def config_path():
    return pathlib.Path(config_dir(), "pdp7_timetracking.config")


class Config:
    def __init__(self):
        self._configparser = configparser.ConfigParser()
        self._configparser.read(config_path())

    def postgres_connection_string(self):
        return self._configparser.get("default", "postgres_connection_string")

    def connection(self):
        return psycopg2.connect(
            self.postgres_connection_string(), options="-c search_path=pdp7_timetracker"
        )


class TimeTracker:
    def __init__(self, config):
        self.config = config

    def query(self, sql, **kwargs):
        with self.config.connection() as connection:
            with connection.cursor(
                cursor_factory=psycopg2.extras.NamedTupleCursor
            ) as cursor:
                cursor.execute(sql, kwargs)
                return cursor.fetchall()

    def dml(self, sql, **kwargs):
        with self.config.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(sql, kwargs)

    def activities(self):
        return self.query("select * from reporting_activities order by id_path")

    def new_activity(self, *args):
        parent = None
        for arg in args:
            self.dml(
                "insert into activities(id, parent_id) values (%(id)s, %(parent_id)s) on conflict do nothing",
                id=arg,
                parent_id=parent,
            )
            parent = arg

    def new_tracked_period(self, activity, lower, upper):
        self.dml(
            "insert into tracked_period(period, activity_id) values (%(range)s, %(activity_id)s)",
            activity_id=activity,
            range=psycopg2.extras.DateTimeTZRange(lower=lower, upper=upper),
        )

    def stop(self, now=None):
        now = now or datetime.datetime.now()
        self.dml(
            "update tracked_period set period = tstzrange(lower(period), %(upper)s) where upper(period) is null",
            upper=now,
        )

    def start(self, activity, now=None):
        self.stop(now=now)
        now = now or datetime.datetime.now()
        self.new_tracked_period(activity, now, None)
