import sys

if sys.version_info >= (3, 8):
    from importlib.metadata import version as get_version
else:
    from importlib_metadata import version as get_version

__version__ = get_version("pyborg")
