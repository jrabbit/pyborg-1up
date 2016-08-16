#!/usr/bin/env python
import logging
import random
import ssl

import baker
import irc
import irc.bot
import irc.strings
import pyborg.pyborg
import toml

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class ModIRC(irc.bot.SingleServerIRCBot):

    def __init__(self, my_pyborg, settings, channel=None, nickname=None, server=None, port=None, **connect_params):
        self.settings = settings
        server = server or self.settings['server']['server']
        port = port or self.settings['server']['port']
        nickname = nickname or self.settings['nickname']
        realname = nickname or self.settings['realname']
        if self.settings['server']['ssl']:
            ssl_factory = irc.connection.Factory(wrapper=ssl.wrap_socket)
            super(ModIRC, self).__init__(
                [(server, port)], nickname, realname, connect_factory=ssl_factory, **connect_params)
        else:
            super(ModIRC, self).__init__(
                [(server, port)], nickname, realname, **connect_params)
        if not self.settings['multiplex']:
            self.my_pyborg = my_pyborg()

    def on_welcome(self, c, e):
        logger.info("Connected to IRC server.")
        # stops timeouts
        c.set_keepalive(5)
        for chan_dict in self.settings['server']['channels']:
            c.join(chan_dict['chan'])
            logger.info("Joined channel: %s", chan_dict['chan'])
    
    def on_nicknameinuse(self, c, e):
        c.nick(c.get_nickname() + "_")

    def strip_nicks(self, body, e):
        "takes a utf-8 body and replaces all nicknames with #nick"
        # copied from irc mod 1
        for x in self.channels[e.target].users():
            body = body.replace(x, "#nick")
        logger.debug("Replaced nicks: %s", body)
        return body

    def learn(self, body):
        "thin wrapper for learn to switch to multiplex mode"
        if not self.settings['multiplex']:
            self.my_pyborg.learn(body)
        elif requests:
            ret = requests.post("http://localhost:2001/learn", data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

    def reply(self, body):
        "thin wrapper for reply to switch to multiplex mode"
        if not self.settings['multiplex']:
            reply = self.my_pyborg.reply(body)
        elif requests:
            ret = requests.post("http://localhost:2001/reply", data={"body": body})
            if ret.status_code == requests.codes.ok:
                reply = ret.text
            elif ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
                return
            else:
                ret.raise_for_status()

        else:
            raise NotImplementedError
        # TODO: replace #nicks here
        return reply


    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.learn(self.strip_nicks(a[1], e).encode('utf-8'))
            msg = self.reply(a[1].encode('utf-8'))
            if msg:
                logger.info("Response: %s", msg)
                c.privmsg(e.target, msg)
        else:
            chans = {z['chan']:z for z in self.settings['server']['channels']}
            logger.debug(type(e.target))
            if self.settings['speaking'] and chans[e.target.lower()]['speaking']:                
                reply_chance_inverse = 100 - chans[e.target.lower()]['reply_chance']
                logger.debug("Inverse Reply Chance = %d", reply_chance_inverse)
                rnd = random.uniform(0,100)
                logger.debug("Random float: %d", rnd)
                if rnd > reply_chance_inverse:
                    msg = self.reply(e.arguments[0].encode('utf-8'))
                    if msg:
                        logger.info("Response: %s", msg)
                        c.privmsg(e.target, msg)
            body = self.strip_nicks(e.arguments[0], e).encode('utf-8')
            self.learn(body)
        return



@baker.command(default=True, shortopts={"verbose": "v", "debug": "d", "conffile": 'f'})
def start_irc_bot(verbose=True, debug=False, conffile="example.irc.toml"):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        # only the first basicConfig() is respected.
    if verbose:
        logging.basicConfig(level=logging.INFO)
    pyb = pyborg.pyborg.pyborg
    settings = toml.load(conffile)
    bot = ModIRC(pyb, settings)
    try:
        bot.start()
    except KeyboardInterrupt:
        if not bot.settings['multiplex']:
            bot.my_pyborg.save_all()
        bot.disconnect("Killed at terminal.")
    except IOError as e:
        if bot.settings['multiplex']:
            logger.error(e)
            logger.info("Is pyborg_http running?")
        else:
            raise
    except Exception as e:
        logger.exception(e)
        if not bot.settings['multiplex']:
            bot.my_pyborg.save_all()
        bot.disconnect("Caught exception")

if __name__ == '__main__':
    baker.run()
