import inspect
import logging

import attr
from pyborg.pyborg import pyborg

logger = logging.getLogger(__name__)

@attr.s
class BottledPyborg():
    brain_path = attr.ib()
    name = "bottled_pyborg"
    api = 2

    def setup(self, app):
        self.pyb = pyborg(self.brain_path)

    def close(self):
        logger.debug("bottled pyborg save via close() initiated.")
        self.pyb.save_brain()

    def apply(self, callback, route):
        keyword = "pyborg"
        args = inspect.signature(route.callback).parameters
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs):
            kwargs[keyword] = self.pyb
            return callback(*args, **kwargs)

        return wrapper
