import pytest
from testcontainers import postgres

import pdp7_timetracker
from pdp7_timetracker import cmd
from pdp7_timetracker import sql


class TestSql(sql.Sql):
    def create_result(self, cursor):
        return cursor.fetchall()


class TestTimeTracker(sql.SqlTimeTracker):
    def __init__(self, time_tracker, database, Sql):
        super().__init__(time_tracker, Sql)
        self.connection = sql.connect(
            database.get_connection_url().replace("+psycopg2", "")
        )

    def _open_connection(self):
        return self.connection

    def _close_connection(self, connection):
        pass


@pytest.fixture(scope="session")
def database():
    with postgres.PostgresContainer("postgres:12") as pg:
        with sql.connect(
            pg.get_connection_url().replace("+psycopg2", "")
        ) as connection:
            with connection.cursor() as cursor:
                cursor.execute(pdp7_timetracker.TimeTracker().get_schema())
        yield pg


@pytest.fixture
def tt(database):
    tt = TestTimeTracker(pdp7_timetracker.TimeTracker(), database, TestSql)
    yield tt
    tt.connection.rollback()


@pytest.fixture
def console_tt(database):
    tt = TestTimeTracker(pdp7_timetracker.TimeTracker(), database, cmd.ConsoleSql)
    yield tt
    tt.connection.rollback()
