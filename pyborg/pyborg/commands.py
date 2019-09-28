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
        ret = requests.get(multi_server + "words.json")
        ret.raise_for_status()
        words = ret.json()
        try:
            contexts_per_word = float(words["contexts"]) / float(words["words"])

        except ZeroDivisionError:
            contexts_per_word = 0

        msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (words["words"], words["contexts"], contexts_per_word, words["lines"])
        return msg

    else:
        raise NotImplementedError


@command(internals=True, pass_msg=True)
def known(multiplex, multi_server, msg=None):
    message = msg.split()[1:]
    logger.info(message)
    ret = requests.get(multi_server + "known?word={}".format(message[0]))
    ret.raise_for_status()
    logger.info(ret.text)
    return ret.text


@command()
def blap():
    return "https://sexyferret.science/blap/its_good_to_be_sad.gif"


@command()
def spray():
    return "https://sexyferret.science/blap/spray.gif"