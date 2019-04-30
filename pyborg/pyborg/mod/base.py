import logging
import sys

import attr
import requests
import toml

logger = logging.getLogger(__name__)


@attr.s
class PyborgModBase(object):
    """Do all the weird stuff for you. This class sets up a toml-backed settings file,
       mutliplexing attributes, and reply/learn wrappers with multiplex (and not!) support
       Required Args: conf_file a path to a toml file (as a string-ish)
       Use with caution in multiple-inheritance situations! (discord.py, irc both inherit from a different base class for example)
       todo: add command support, tests, entrypoint helpers
    """
    conf_file = attr.ib()  # path-like
    settings = attr.ib(default=None, type=dict)
    multiplexing = attr.ib(type=bool, default=True)
    multi_port = attr.ib(type=int, default=2001)
    multi_server = attr.ib(type=str, default="localhost")
    pyborg = attr.ib(default=None)

    def __attrs_post_init__(self):
        try:
            self.settings = toml.load(self.conf_file)
            self.multiplexing = self.settings['pyborg']['multiplex']
            self.multi_server = self.settings['pyborg']['multiplex_server']
            self.multi_port = self.settings['pyborg']['multiplex_port']
        except (KeyError, OSError):
            logger.info("Missing config [keys], you get defaults.")
            logger.debug("Config error we got", exc_info=True)

        if not self.multiplexing:
            import pyborg.pyborg
            self.pyborg = pyborg.pyborg.pyborg()
        else:
            self._check_http()

    def _check_http(self):
        try:
            ret = requests.get("http://{}:{}".format(self.multi_server, self.multi_port))
        except requests.exceptions.ConnectionError:
            logger.error("connection to pyborg server failed!")
            sys.exit(2001)
        ret.raise_for_status()


    def learn(self, body):
        """multiplex mode-enabled learn wrapper"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:{}/learn".format(self.multi_server, self.multi_port), data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()
        else:
            self.pyborg.learn(body)

    def reply(self, body):
        """multiplex mode-enabled reply wrapper"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:{}/reply".format(self.multi_server, self.multi_port), data={"body": body})
            if ret.status_code == requests.codes.ok:
                reply = ret.text
                logger.debug("got reply: %s", reply)
            elif ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
                return None
            else:
                ret.raise_for_status()
            return reply
        else:
            return self.pyborg.reply(body)

    def save(self):
        "base class save method"
        if self.multiplexing:
            logger.info("saving from multiplex-enabled mods may be slow or bad, you should probably do this from the commandline.")
            ret = requests.post("http://{}:{}/save".format(self.multi_server, self.multi_port))
            ret.raise_for_status()
        else:
            self.pyborg.save_brain()
