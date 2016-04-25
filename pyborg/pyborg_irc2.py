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


class ModIRC(irc.bot.SingleServerIRCBot):

    def __init__(self, my_pyborg, channel=None, nickname=None, server=None, port=None, **connect_params):
        self.settings = toml.load("example.irc.toml")
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
        self.my_pyborg = my_pyborg

    def on_welcome(self, c, e):
        logging.info("Connected to IRC server.")
        # stops timeouts
        c.set_keepalive(5)
        for chan_dict in self.settings['server']['channels']:
            c.join(chan_dict['chan'])
            logging.info("Joined channel: %s", chan_dict['chan'])

    def on_pubmsg(self, c, e):
        a = e.arguments[0].split(":", 1)
        if len(a) > 1 and irc.strings.lower(a[0]) == irc.strings.lower(self.connection.get_nickname()):
            self.my_pyborg.learn(a[1].encode('utf-8'))
            msg = self.my_pyborg.reply(a[1])
            if msg:
                logging.info("Response: %s", msg)
                c.privmsg(e.target, msg)
        else:
            chans = {z['chan']:z for z in self.settings['server']['channels']}
            if self.settings['speaking'] and chans[e.target.lower()]['speaking']:                
                reply_chance_inverse = 100 - chans[e.target.lower()]['reply_chance']
                logging.debug("Inverse Reply Chance = %d", reply_chance_inverse)
                rnd = random.uniform(0,100)
                logging.debug("Random float: %d", rnd)
                if rnd > reply_chance_inverse:
                    msg = self.my_pyborg.reply(e.arguments[0].encode('utf-8'))
                    if msg:
                        logging.info("Response: %s", msg)
                        c.privmsg(e.target, msg)

            self.my_pyborg.learn(e.arguments[0].encode('utf-8'))

        return


@baker.command(default=True, shortopts={"verbose": "v", "debug": "d"})
def start_irc_bot(verbose=True, debug=False):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
        # only the first basicConfig() is respected.
    if verbose:
        logging.basicConfig(level=logging.INFO)
    pyb = pyborg.pyborg.pyborg()
    bot = ModIRC(pyb)
    try:
        bot.start()
    except KeyboardInterrupt:
        pyb.save_all()
        bot.disconnect("Default disconnect message")
    except Exception:
        pyb.save_all()
        raise

if __name__ == '__main__':
    baker.run()
