import logging
import re

logger = logging.getLogger(__name__)

def normalize_awoos(inp):
    "Takes an awoo of varying length and trims it."
    # https://docs.python.org/2/library/re.html#text-munging
    def repl(m):
        m.group()
        return "awoo"
    pattern = r"awo+" 
    out = re.sub(pattern, repl, inp)
    return out