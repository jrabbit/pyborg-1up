import sys
import logging

import arrow
import requests
import baker
import toml

import discord
import asyncio

import pyborg.pyborg

#https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/bot.py#L146

logger = logging.getLogger(__name__)

class PyborgDiscord(discord.Client):
    """docstring for PyborgDiscord"""
    def __init__(self, toml_file):
        super(PyborgDiscord, self).__init__()
        self.toml_file = toml_file
        self.settings = toml.load(self.toml_file)
        self.multiplexing = self.settings['pyborg']['multiplex']
        if not self.multiplexing:
            # self.pyborg = pyborg.pyborg.pyborg()
            # pyb config parsing isn't ready for python 3.
            raise NotImplementedError
        else:
            self.pyborg = None

    def our_start(self):
        self.run(self.settings['discord']['token'])

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        print("enter on_message")
        """message.content  ~= <@221134985560588289> you should play dota"""
        logger.debug(message.content)
        print(message.content)
        if self.settings['discord']['learning']:
            self.learn(message.content)
        if message.content.startswith("<@{}>".format(self.user.id)):
            msg = self.reply(message.content)
            logger.debug("on message: %s" % msg)
            if msg:
                print("Sending message...")
                await self.send_message(message.channel, msg)

    def learn(self, body):
        """thin wrapper for learn to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://localhost:2001/learn", data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

    def reply(self, body):
        """thin wrapper for reply to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://localhost:2001/reply", data={"body": body})
            if ret.status_code == requests.codes.ok:
                reply = ret.text
                logger.debug("got reply: %s", reply)
            elif ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
                return
            else:
                ret.raise_for_status()
            return reply

    def teardown(self):
        pass


@baker.command(default=True, shortopts={"debug": "d", "verbose": "v", "toml_conf": "f"})
def start_discord_bot(verbose=True, debug=False, toml_conf="example.discord.toml"):
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)
    bot = PyborgDiscord(toml_conf)
    try:
        bot.our_start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise

if __name__ == '__main__':
    baker.run()