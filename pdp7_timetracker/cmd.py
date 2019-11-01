import configparser
import datetime
import inspect
import os
import pathlib

import appdirs
import IPython
import psycopg2.extras
import tabulate


import pdp7_timetracker


def config_dir():
    return appdirs.user_config_dir("pdp7_timetracking")


def config_path():
    return pathlib.Path(config_dir(), "pdp7_timetracking.config")


class Config:
    def __init__(self):
        self._configparser = configparser.ConfigParser()
        self._configparser.read(config_path())

    def postgres_connection_string(self):
        return self._configparser.get(
            os.environ.get("TITR", "default"), "postgres_connection_string"
        )

    def connection(self):
        return psycopg2.connect(
            self.postgres_connection_string(), options="-c search_path=pdp7_timetracker"
        )


class ConsoleQueryResult:
    def __init__(self, rows, description):
        self.rows = rows
        self.description = description

    def __repr__(self):
        return tabulate.tabulate(self.rows, headers=[c.name for c in self.description])


class Sql:
    def __init__(self, config):
        self.connection = config.connection()

    def query(self, sql, **kwargs):
        with self.connection.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            cursor.execute(sql, kwargs)
            return ConsoleQueryResult(cursor.fetchall(), cursor.description)

    def ddl(self, sql, **kwargs):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, kwargs)

    def dml(self, sql, **kwargs):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, kwargs)

    def commit(self):
        self.connection.commit()
        self.connection.close()

    def rollback(self):
        self.connection.rollback()
        self.connection.close()


class ConsoleTimeTracker:
    def __init__(self, config):
        self.config = config
        self.time_tracker = pdp7_timetracker.TimeTracker()

    def __getattr__(self, name):
        wrapped = getattr(self.time_tracker, name)
        signature = inspect.signature(wrapped)

        def _wrapped(*args, **kwargs):
            excepted = False
            try:
                if "sql" in signature.parameters:
                    kwargs["sql"] = Sql(self.config)
                if "now" in signature.parameters:
                    kwargs["now"] = datetime.datetime.now()
                return wrapped(*args, **kwargs)
            except Exception:
                if "sql" in kwargs:
                    kwargs["sql"].rollback()
                raise
            finally:
                if not excepted and "sql" in kwargs:
                    kwargs["sql"].commit()

        return _wrapped

    def __dir__(self):
        return dir(self.time_tracker)


def main():
    config = Config()
    print(config.postgres_connection_string())
    tt = ConsoleTimeTracker(config)
    tt  # is put into ipython context
    IPython.embed()


if __name__ == "__main__":
    main()
