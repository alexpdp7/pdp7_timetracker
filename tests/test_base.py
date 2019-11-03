import collections
import datetime

import pytest
from testcontainers import postgres

import pdp7_timetracker
from pdp7_timetracker import sql


class TestSql(sql.Sql):
    def create_result(self, cursor):
        return cursor.fetchall()


class TestTimeTracker(sql.SqlTimeTracker):
    def __init__(self, time_tracker, database):
        super().__init__(time_tracker, TestSql)
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
    tt = TestTimeTracker(pdp7_timetracker.TimeTracker(), database)
    yield tt
    tt.connection.rollback()


def test_new_activity(tt):
    tt.new_activity("foo")
    tt.new_activity("bar")
    tt.new_activity("foo", "baz")
    Record = collections.namedtuple("Record", ["id", "parent_id", "id_path"])
    assert tt.activities() == [
        Record(id="bar", parent_id=None, id_path="bar"),
        Record(id="foo", parent_id=None, id_path="foo"),
        Record(id="baz", parent_id="foo", id_path="foo / baz"),
    ]


def test_start_stop(tt):
    tt.new_activity("foo")
    tt.start("foo", now=datetime.datetime(2019, 11, 2, 10, 0))
    tt.stop(now=datetime.datetime(2019, 11, 2, 10, 10))
    Record = collections.namedtuple("Record", ["id_path", "total"])
    assert tt.daily_report(day=datetime.date(2019, 11, 2)) == [
        Record(id_path="foo", total=datetime.timedelta(seconds=600))
    ]
