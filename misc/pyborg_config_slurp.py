import logging
import pprint
from pathlib import Path

import attr
import toml


for f in Path("pyborg").glob("*.toml"):
    with open(f) as fd:
        s = toml.load(fd)
        print(f, "=")
        pprint.pprint(s)