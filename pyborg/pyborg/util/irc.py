import venusian


def command(internals=False):
    """Wraps a python function into an irc command"""

    def decorator(wrapped):

        def callback(scanner, name, ob):
            scanner.registry.add(name, ob, internals)

        venusian.attach(wrapped, callback)
        return wrapped

    return decorator
