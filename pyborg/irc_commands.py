import requests

from pyborg.util.irc import command
from pyborg.pyborg import pyborg


@command()
def info():
    """Returns version number and source code link"""
    return "{}. My source can be found at https://github.com/jrabbit/pyborg-1up".format(pyborg.ver_string)

@command(internals=True)
def words(multiplex, multi_server):
    """Returns the number of words known and contexts per word"""
    if multiplex:
        ret = requests.get(multi_server+"words.json")
        ret.raise_for_status()
        words = ret.json()
        if words["contexts"] is not 0 and words["words"] is not 0:
            contexts_per_word = float(words["contexts"]) / float(words["words"])
        else:
            contexts_per_word = 0.0
        msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (words["words"], words["contexts"], contexts_per_word, words["lines"])
        return msg
    else:
        raise NotImplementedError
