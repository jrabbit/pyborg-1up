import logging
import random
from importlib.resources import open_text

import requests

import pyborg

from .util.commands import command

logger = logging.getLogger(__name__)


@command()
def info() -> str:
    """Returns version number and source code link"""
    return "I am a version {} Pyborg. My source can be found at https://github.com/jrabbit/pyborg-1up".format(pyborg.__version__)


@command(internals=True)
def words(multiplex: bool, multi_server: str) -> str:
    """Returns the number of words known and contexts per word"""
    if multiplex:
        ret = requests.get(multi_server + "words.json")
        ret.raise_for_status()
        payload = ret.json()
        try:
            contexts_per_word = float(payload["contexts"]) / float(payload["words"])

        except ZeroDivisionError:
            contexts_per_word = 0

        msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (payload["words"], payload["contexts"], contexts_per_word, payload["lines"])
        return msg

    else:
        raise NotImplementedError


@command(internals=True, pass_msg=True)
def known(multiplex: bool, multi_server: str, msg: str = "") -> str:  # pylint:disable=unused-argument
    message = msg.split()[1:]
    logger.info(message)
    ret = requests.get(multi_server + "known?word={}".format(message[0]))
    ret.raise_for_status()
    logger.info(ret.text)
    return ret.text


@command()
def blap() -> str:
    return "https://sexyferret.science/blap/its_good_to_be_sad.gif"


@command()
def spray() -> str:
    return "https://sexyferret.science/blap/spray.gif"

@command()
def sickos() -> str:
    return "https://sexyferret.science/blap/sickos.jpg"

@command()
def lockthemup() -> str:
    return "https://sexyferret.science/blap/lockhimup.gif"

@command()
def italian() -> str:
    ITALIAN_FIRSTNAMES = open_text("pyborg.util", "elenco_cognomi.txt").readlines()
    ITALIAN_LASTNAMES = open_text("pyborg.util", "elenco_nomi.txt").readlines()
    return random.choice(ITALIAN_FIRSTNAMES).strip() + " " + random.choice(ITALIAN_LASTNAMES).strip()
