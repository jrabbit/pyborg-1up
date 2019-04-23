import logging
import re

logger = logging.getLogger(__name__)


def normalize_awoos(inp: str) -> str:
    "Takes an awoo of varying length and trims it."
    # https://docs.python.org/2/library/re.html#text-munging
    pattern = re.compile(r"(?i)awo+")
    out = pattern.sub("awoo", inp)
    return out
