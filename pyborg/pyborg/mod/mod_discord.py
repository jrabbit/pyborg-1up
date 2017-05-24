import asyncio
import logging
import sys
from functools import partial

import arrow
import baker
import discord
import requests
import toml
import venusian

import pyborg.commands

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
        self.settings = toml.load(self.toml_file)
        self.multiplexing = self.settings['pyborg']['multiplex']
        self.multi_server = self.settings['pyborg']['multiplex_server']
        self.registry = Registry(self)
        if not self.multiplexing:
            # self.pyborg = pyborg.pyborg.pyborg()
            # pyb config parsing isn't ready for python 3.
            raise NotImplementedError
        else:
            self.pyborg = None

    def our_start(self):
        self.scan()
        if 'token' in self.settings['discord']:
            self.run(self.settings['discord']['token'])
        else:
            logger.error("No Token. Set one in your conf file.")

    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def clean_msg(self, message):
        return ' '.join(message.content.split()[1:])

    async def on_message(self, message):
        """message.content  ~= <@221134985560588289> you should play dota"""
        logger.debug(message.content)
        if message.content[0] == "!":
            command_name = message.content[1:]
            if command_name in  ["list", "help"]:
                help_text = "I have a bunch of commands: "
                for k, v in self.registry.registered.items():
                    help_text += "!{}".format(k)
                await self.send_message(message.channel, help_text)
            else:
                if command_name in self.registry.registered:
                    command = self.registry.registered[command_name]
                    logger.info("Running command %s", command)
                    await self.send_message(message.channel, command())
        
        if self.settings['discord']['learning']:
            self.learn(message.content)
        if message.content.startswith("<@{}>".format(self.user.id)):
            clean = self.clean_msg(message)
            msg = self.reply(clean)
            logger.debug("on message: %s" % msg)
            if msg:
                logger.debug("Sending message...")
                msg = msg.replace("#nick", str(message.author.mention))
                await self.send_message(message.channel, msg)

    def learn(self, body):
        """thin wrapper for learn to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

    def reply(self, body):
        """thin wrapper for reply to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            ret = requests.post("http://{}:2001/reply".format(self.multi_server), data={"body": body})
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

    def scan(self, module=pyborg.commands):
        self.scanner = venusian.Scanner(registry=self.registry)
        self.scanner.scan(module)
