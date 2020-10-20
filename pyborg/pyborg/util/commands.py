"command loading utils for the venusian powered decorator registry pattern"
from typing import Callable, Dict
from pathlib import Path
import logging

import venusian
import toml

logger = logging.getLogger(__name__)


def command(internals: bool = False, pass_msg: bool = False) -> Callable:
    """Wraps a python function into an irc command"""

    def decorator(wrapped: Callable) -> Callable:
        def callback(scanner: venusian.Scanner, name: str, ob: Callable) -> None:
            scanner.registry.add(name, ob, internals, pass_msg)

        venusian.attach(wrapped, callback)
        return wrapped

    return decorator


def load_simple_commands(directory: Path) -> Dict[str, Callable]:
    "load simple commands"
    out: Dict[str, Callable] = dict()
    files = directory.glob("*.toml")
    for f in files:
        with open(f) as fd:
            dx = toml.load(fd)
            out.update(dx)
    return out
