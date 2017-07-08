import attr
import inspect
from pyborg.pyborg import pyborg
@attr.s
class BottledPyborg(object):
    brain_path = attr.ib()
    name = "bottled_pyborg"
    api = 2

    def setup(self, app):
        self.pyb = pyborg(self.brain_path)

    def close(self):
        self.pyb.save_all()
        
    def apply(self, callback, route):
        keyword = "pyborg"
        args = inspect.getargspec(route.callback)[0]
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[keyword] = self.pyb
            return callback(*args, **kwargs)

        return wrapper