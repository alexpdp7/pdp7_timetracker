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
    assert tt.daily_report(day=datetime.date(2019, 11, 2)) == [
        Record(id_path="foo", total=datetime.timedelta(seconds=600))
    ]
