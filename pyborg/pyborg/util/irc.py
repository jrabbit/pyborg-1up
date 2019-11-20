from typing import Callable

import venusian


def command(internals:bool=False, pass_msg:bool=False) -> Callable:
    """Wraps a python function into an irc command"""

    def decorator(wrapped: Callable) -> Callable:

        def callback(scanner: venusian.Scanner, name: str, ob: Callable) -> None:
            scanner.registry.add(name, ob, internals, pass_msg)

        venusian.attach(wrapped, callback)
        return wrapped

    return decorator
