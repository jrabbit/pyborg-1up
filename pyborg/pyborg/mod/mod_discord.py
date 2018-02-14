import logging
from functools import partial
from typing import Union, Dict

import discord
import requests
import toml
import venusian

import pyborg.commands
from pyborg.util.awoo import normalize_awoos


#https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/bot.py#L146

logger = logging.getLogger(__name__)

class Registry(object):
    """Command registry of decorated pyborg commands"""
    def __init__(self, mod):
        self.registered = {}
        self.mod = mod

    def add(self, name, ob, internals):
        if internals:
            self.registered[name] = partial(ob, self.mod.multiplexing,  multi_server="http://{}:2001/".format(self.mod.multi_server))
        else:
            self.registered[name] = ob


class PyborgDiscord(discord.Client):
    """docstring for PyborgDiscord"""
    def __init__(self, toml_file):
        super(PyborgDiscord, self).__init__()
        self.toml_file = toml_file
        self.settings: Dict = toml.load(self.toml_file)
        self.multiplexing = self.settings['pyborg']['multiplex']
        self.multi_server = self.settings['pyborg']['multiplex_server']
        self.registry = Registry(self)
        if not self.multiplexing:
            # self.pyborg = pyborg.pyborg.pyborg()
            # pyb config parsing isn't ready for python 3.
            raise NotImplementedError
        else:
            self.pyborg = None

    def our_start(self) -> None:
        self.scan()
        if 'token' in self.settings['discord']:
            self.run(self.settings['discord']['token'])
        else:
            logger.error("No Token. Set one in your conf file.")

    async def on_ready(self) -> None:
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def clean_msg(self, message: discord.Message) -> str:
        return ' '.join(message.content.split())

    async def on_message(self, message) -> None:
        """message.content  ~= <@221134985560588289> you should play dota"""
        logger.debug(message.content)
        if message.content and message.content[0] == "!":
            command_name = message.content[1:]
            if command_name in  ["list", "help"]:
                help_text = "I have a bunch of commands:"
                for k, v in self.registry.registered.items():
                    help_text += " !{}".format(k)
                await self.send_message(message.channel, help_text)
            else:
                if command_name in self.registry.registered:
                    command = self.registry.registered[command_name]
                    logger.info("Running command %s", command)
                    await self.send_message(message.channel, command())
        if message.author == self.user:
            logger.info("Not learning/responding to self")
            return

        # Custom Emoji handling here
        # DEBUG:pyborg.mod.mod_discord:<:weedminion:392111795642433556>
        # e = message.server.emojis
        # logger.info(str([x.name for x in e]))

        #s[s.find("<:"):s.find(">")+1]

        message.content[message.content.find("<:"):message.content.find(">")+1]


        # Strip nicknames for pyborg
        l = list()
        for x in message.content.split(): 
            if x.startswith("<@!"):
                x = "#nick"
            l.append(x)

        logger.debug(str(l))
        line = " ".join(l)
        line = normalize_awoos(line)

        if self.settings['discord']['learning']:
            self.learn(line)

        if self.user.mentioned_in(message):
            await self.send_typing(message.channel)
            msg = self.reply(line)
            logger.debug("on message: %s" % msg)
            if msg:
                logger.debug("Sending message...")
                # if custom emoji: replace to <:weedminion:392111795642433556>
                # message.server map to full custom emoji
                emoji_map = {x.name:x for x in message.server.emojis}
                for word in msg.split():
                    if word in emoji_map:
                        e = emoji_map[word]
                        msg = msg.replace(word, "<:{}:{}>".format(e.name, e.id))
                msg = msg.replace("#nick", str(message.author.mention))
                msg = msg.replace("@everyone", "`@everyone`")
                msg = msg.replace("@here", "`@here`")
                await self.send_message(message.channel, msg)

    def learn(self, body: str) -> None:
        """thin wrapper for learn to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

    def reply(self, body: str) -> Union[str, None]:
        """thin wrapper for reply to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:2001/reply".format(self.multi_server), data={"body": body})
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
            raise NotImplementedError

    def teardown(self) -> None:
        pass

    def scan(self, module=pyborg.commands) -> None:
        self.scanner = venusian.Scanner(registry=self.registry)
        self.scanner.scan(module)
