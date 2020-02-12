import collections
import datetime


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
    later = datetime.datetime(2019, 11, 3)
    assert tt.daily_report(day=datetime.date(2019, 11, 2), now=later) == [
        Record(id_path="foo", total=datetime.timedelta(seconds=600))
    ]


def test_start_stop_multiple_activities(tt):
    tt.new_activity("foo")
    tt.new_activity("bar")
    tt.start("foo", "bar", now=datetime.datetime(2019, 11, 2, 10, 0))
    tt.stop(now=datetime.datetime(2019, 11, 2, 10, 10))
    Record = collections.namedtuple("Record", ["id_path", "total"])
    later = datetime.datetime(2019, 11, 3)
    assert tt.daily_report(day=datetime.date(2019, 11, 2), now=later) == [
        Record(id_path="bar", total=datetime.timedelta(seconds=600)),
        Record(id_path="foo", total=datetime.timedelta(seconds=600)),
    ]


def test_reporting_across_days(tt):
    tt.new_activity("foo")
    tt.start("foo", now=datetime.datetime(2019, 11, 2, 23, 0))
    tt.stop(now=datetime.datetime(2019, 11, 3, 1, 00))
    Record = collections.namedtuple("Record", ["id_path", "total"])
    later = datetime.datetime(2019, 11, 5)
    assert tt.daily_report(day=datetime.date(2019, 11, 2), now=later) == [
        Record(id_path="foo", total=datetime.timedelta(seconds=3600))
    ]
    assert tt.daily_report(day=datetime.date(2019, 11, 3), now=later) == [
        Record(id_path="foo", total=datetime.timedelta(seconds=3600))
    ]


def test_reporting_unended(tt):
    tt.new_activity("foo")
    tt.start("foo", now=datetime.datetime(2019, 11, 2, 11, 0))
    Record = collections.namedtuple("Record", ["id_path", "total"])
    assert tt.daily_report(
        day=datetime.date(2019, 11, 2), now=datetime.datetime(2019, 11, 2, 12, 0)
    ) == [Record(id_path="foo", total=datetime.timedelta(seconds=3600))]


def test_tabulation(console_tt):
    console_tt.new_activity("foo")
    expected = """id    parent_id    id_path
----  -----------  ---------
foo                foo"""
    assert repr(console_tt.activities()) == expected
