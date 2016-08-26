import requests
import toml

from pyborg_irc2 import command
from pyborg.pyborg import pyborg


# pyb = pyborg
settings = toml.load("example.irc.toml")
# modirc = ModIRC(pyb, settings)

@command()
def info():
    """Returns version number and source code link"""
    return "{}. My source can be found at https://github.com/jrabbit/pyborg-1up".format(pyborg.ver_string)

@command(internals=True)
def words():
    """Returns the number of words known and contexts per word"""
    if settings['multiplex']:
        ret = requests.get(multi_server+"/words.json")
        words = ret.json()

        msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (words["num_w"], words["num_c"], words["num_cpw"], words["num_l"])
        return msg
    else:
        raise NotImplementedError
