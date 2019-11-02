import configparser
import os
import pathlib

import appdirs
import IPython
import tabulate


import pdp7_timetracker
from pdp7_timetracker import now
from pdp7_timetracker import sql


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
        return sql.connect(self.postgres_connection_string())


class ConsoleTimeTracker(sql.SqlTimeTracker):
    def __init__(self, time_tracker, Sql, config):
        super().__init__(time_tracker, Sql)
        self.config = config

    def _open_connection(self):
        return self.config.connection()

    def _close_connection(self, connection):
        connection.commit()
        connection.close()


class ConsoleQueryResult:
    def __init__(self, cursor):
        self.rows = cursor.fetchall()
        self.headers = [c.name for c in cursor.description]

    def __repr__(self):
        return tabulate.tabulate(self.rows, headers=self.headers)


class ConsoleSql(sql.Sql):
    def create_result(self, cursor):
        return ConsoleQueryResult(cursor)


def main():
    config = Config()
    print(config.postgres_connection_string())
    tt = ConsoleTimeTracker(
        now.NowTimeTracker(pdp7_timetracker.TimeTracker()), ConsoleSql, config
    )
    tt  # is put into ipython context
    IPython.embed()


if __name__ == "__main__":
    main()
