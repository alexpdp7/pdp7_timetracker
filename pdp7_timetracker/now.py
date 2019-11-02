import datetime
import functools
import inspect


class NowTimeTracker:
    def __init__(self, time_tracker):
        self.time_tracker = time_tracker

    def __getattr__(self, name):
        wrapped = getattr(self.time_tracker, name)
        signature = inspect.signature(wrapped)

        def _wrapped(*args, **kwargs):
            if "now" in signature.parameters and "now" not in kwargs:
                return wrapped(*args, **kwargs, now=datetime.datetime.now())
            return wrapped(*args, **kwargs)

        functools.update_wrapper(_wrapped, wrapped)

        return _wrapped

    def __dir__(self):
        return dir(self.time_tracker)
