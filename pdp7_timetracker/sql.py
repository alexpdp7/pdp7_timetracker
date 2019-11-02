import abc
import functools
import inspect

import psycopg2.extras


def connect(connection_string):
    return psycopg2.connect(
        connection_string, options="-c search_path=pdp7_timetracker"
    )


class Sql(abc.ABC):
    def __init__(self, connection):
        self.connection = connection

    @abc.abstractmethod
    def create_result(self, cursor):
        pass

    def query(self, sql, **kwargs):
        with self.connection.cursor(
            cursor_factory=psycopg2.extras.NamedTupleCursor
        ) as cursor:
            cursor.execute(sql, kwargs)
            return self.create_result(cursor)

    def ddl(self, sql, **kwargs):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, kwargs)

    def dml(self, sql, **kwargs):
        with self.connection.cursor() as cursor:
            cursor.execute(sql, kwargs)


class SqlTimeTracker(abc.ABC):
    def __init__(self, time_tracker, Sql):
        self.time_tracker = time_tracker
        self.Sql = Sql

    @abc.abstractmethod
    def _open_connection(self):
        pass

    @abc.abstractmethod
    def _close_connection(self, connection):
        pass

    def __getattr__(self, name):
        wrapped = getattr(self.time_tracker, name)
        signature = inspect.signature(wrapped)

        def _wrapped(*args, **kwargs):
            if "sql" in signature.parameters:
                connection = self._open_connection()
                try:
                    sql = self.Sql(connection)
                    return wrapped(*args, **kwargs, sql=sql)
                finally:
                    self._close_connection(connection)
            return wrapped(*args, **kwargs)

        functools.update_wrapper(_wrapped, wrapped)
        return _wrapped

    def __dir__(self):
        return dir(self.time_tracker)
