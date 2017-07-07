import logging

import requests

from .util.irc import command

import pyborg

logger = logging.getLogger(__name__)



@command()
def info():
    """Returns version number and source code link"""
    return "I am a version {} Pyborg. My source can be found at https://github.com/jrabbit/pyborg-1up".format(pyborg.__version__)

@command(internals=True)
def words(multiplex, multi_server):
    """Returns the number of words known and contexts per word"""
    if multiplex:
        ret = requests.get(multi_server+"words.json")
        ret.raise_for_status()
        words = ret.json()
        try:
            contexts_per_word = float(words["words"]) / float(words["contexts"])

        except ZeroDivisionError:
            contexts_per_word = 0

        msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (words["words"], words["contexts"], contexts_per_word, words["lines"])
        return msg

    else:
        raise NotImplementedError
