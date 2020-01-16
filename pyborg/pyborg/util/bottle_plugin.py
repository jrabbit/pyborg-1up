import inspect
import logging
from typing import Callable
from pathlib import Path

import attr
import click
from filelock import FileLock

from pyborg.pyborg import pyborg

folder = click.get_app_dir("Pyborg")
logger = logging.getLogger(__name__)
SAVE_LOCK = FileLock(Path(folder, ".pyborg_is_saving.lock"))

@attr.s
class BottledPyborg():
    brain_path = attr.ib()
    name = "bottled_pyborg"
    api = 2

    def setup(self, app) -> None:
        self.pyb = pyborg(self.brain_path)

    def close(self) -> None:
        logger.debug("bottled pyborg save via close() initiated.")
        with SAVE_LOCK:
            self.pyb.save_brain()

    def apply(self, callback, route) -> Callable:
        keyword = "pyborg"
        args = inspect.signature(route.callback).parameters
        if keyword not in args:
            return callback

        def wrapper(*args, **kwargs) -> Callable:
            kwargs[keyword] = self.pyb
            return callback(*args, **kwargs)

        return wrapper
