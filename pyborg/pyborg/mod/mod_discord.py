import asyncio
import re
import logging
from functools import partial
from typing import Dict, Union, List, Optional, Callable, MutableMapping, Any
from types import ModuleType

import discord
import aiohttp
import toml
import venusian
import attr

import pyborg
import pyborg.commands as builtin_commands
from pyborg.util.awoo import normalize_awoos


logger = logging.getLogger(__name__)


@attr.s
class PyborgDiscord(discord.Client):
    """This is the pyborg discord client module.
    It connects over http to a running pyborg/http service."""
    toml_file: str = attr.ib()  # any old path
    multi_port: int = attr.ib(default=2001)
    multiplexing: bool = attr.ib(default=True)
    multi_server: str = attr.ib(default="localhost")
    multi_protocol: str = attr.ib(default="http")
    registry: Registry = attr.ib(default=attr.Factory(lambda self: Registry(self), takes_self=True))
    aio_session: aiohttp.ClientSession = attr.ib(init=False)
    save_status_count: int = attr.ib(default=0, init=False)
    pyborg: Optional[pyborg.pyborg.pyborg] = attr.ib(default=None)
    scanner: venusian.Scanner = attr.ib(default=None)
    loop: Optional[asyncio.BaseEventLoop] = attr.ib(default=None)
    settings: MutableMapping[str, Any] = attr.ib(default=None)

    def __attrs_post_init__(self) -> None:
        self.settings = toml.load(self.toml_file)
        try:
            self.multiplexing = self.settings['pyborg']['multiplex']
            self.multi_server = self.settings['pyborg']['multiplex_server']
            self.multi_port = self.settings['pyborg']['multiplex_port']
        except KeyError:
            logger.info("Missing config key, you get defaults.")
        if not self.multiplexing:
            # self.pyborg = pyborg.pyborg.pyborg()
            # pyb config parsing isn't ready for python 3.
            raise NotImplementedError
        else:
            self.pyborg = None
        self.aio_session = aiohttp.ClientSession()
        super().__init__(loop=self.loop)  # this might create a asyncio.loop!

    def our_start(self) -> None:
        "launch discord.Client main event loop (calls Client.run)"

        self.scan()
        if 'token' in self.settings['discord']:
            self.run(self.settings['discord']['token'])
        else:
            logger.error("No Token. Set one in your conf file.")

    async def fancy_login(self) -> None:
        if 'token' in self.settings['discord']:
            await self.login(self.settings['discord']['token'])
        else:
            logger.error("No Token. Set one in your conf file.")

    async def on_ready(self) -> None:
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    def clean_msg(self, message: discord.Message) -> str:
        return ' '.join(message.content.split())

    def _extract_emoji(self, msg: str, server_emojis: List[str]) -> str:
        """extract an emoji, returns a str ready to be munged"""
        # s[s.find("<:"):s.find(">")+1] the general idea here
        start = msg.find("<:")
        attempted_emoji = msg[start + 2: msg.find(":", start + 2)]
        logger.debug("_extract_emoji:attempting to emoji: %s", attempted_emoji)
        if attempted_emoji in server_emojis:
            # now replace the range from start to end with the extracted emoji
            end = msg.find(">", start) + 1
            before, _, after = msg.partition(msg[start:end])
            logger.debug(_)
            incoming_message = before + attempted_emoji + after
            logger.debug(incoming_message)
            return incoming_message
        else:
            # this can be a fancy nitro emoji.
            logger.info("_extract_emoji:someone did a fucky wucky")
            logger.debug("_extract_emoji:OOPSIE WOOPSIE!! Uwu We made a fucky wucky!! A wittle fucko boingo! The code monkeys at our headquarters are working VEWY HAWD to fix this!")
            return msg

    async def on_message(self, message: discord.Message) -> None:
        """message.content  ~= <@221134985560588289> you should play dota"""
        logger.debug(message.content)
        if message.content and message.content[0] == "!":
            command_name = message.content.split()[0][1:]
            if command_name in ["list", "help"]:
                help_text = "I have a bunch of commands:"
                for k, _ in self.registry.registered.items():
                    help_text += " !{}".format(k)
                await message.channel.send(help_text)
            else:
                if command_name in self.registry.registered:
                    command = self.registry.registered[command_name]
                    logger.info("Running command %s", command)
                    logger.info("pass message?: %s", command.pass_msg)
                    if command.pass_msg:
                        await message.channel.send(command(msg=message.content))
                    else:
                        await message.channel.send(command())
        if message.author == self.user:
            logger.debug("Not learning/responding to self")
            return

        if self.save_status_count % 5:
            async with self.aio_session.get(f"http://{self.multi_server}:{self.multi_port}/meta/status.json", raise_for_status=True) as ret_status:
                data = await ret_status.json()
                if data["status"]:
                    await self.change_presence(activity=discord.Game("Saving brain..."))
                else:
                    await self.change_presence(activity=discord.Game("hack the planet"))

        self.save_status_count += 1

        # Custom Emoji handling here
        # DEBUG:pyborg.mod.mod_discord:<:weedminion:392111795642433556>
        # is this cached? is this fast? who the fuck knows
        if "<:" in message.content:
            emojis_possible = message.guild.emojis
            server_emojis = [x.name for x in emojis_possible]
            logger.debug("got server emojis as: %s", str(server_emojis))
            incoming_message = self._extract_emoji(message.content, server_emojis)
        else:
            incoming_message = message.content

        # Strip nicknames for pyborg
        line_list = list()
        for chunk in incoming_message.split():
            if chunk.startswith("<@!"):
                chunk = "#nick"
            line_list.append(chunk)

        line = " ".join(line_list)
        try:
            if self.settings["discord"]["plaintext_ping"]:
                exp = re.compile(message.guild.me.display_name, re.IGNORECASE)
                line = exp.sub("#nick", line)
        except KeyError:
            pass

        logger.debug("post nick replace: %s", line)
        line = normalize_awoos(line)

        if self.settings['discord']['learning']:
            await self.learn(line)

        if self.user.mentioned_in(message) or self._plaintext_name(message):
            async with message.channel.typing():
                msg = await self.reply(line)
                logger.debug("on message: %s", msg)
                if msg:
                    logger.debug("Sending message...")
                    # if custom emoji: replace to <:weedminion:392111795642433556>
                    # message.server map to full custom emoji
                    # TODO: measure time spent here?
                    emoji_map = {x.name: x for x in message.guild.emojis}
                    for word in msg.split():
                        if word in emoji_map:
                            e = emoji_map[word]
                            msg = msg.replace(word, "<:{}:{}>".format(e.name, e.id))
                    msg = msg.replace("#nick", str(message.author.mention))
                    msg = msg.replace("@everyone", "`@everyone`")
                    msg = msg.replace("@here", "`@here`")
                    await message.channel.send(msg)

    def _plaintext_name(self, message: discord.Message) -> bool:
        "returns true if should ping with plaintext nickname per-server if configured"
        try:
            if self.settings["discord"]["plaintext_ping"]:
                return message.guild.me.display_name.lower() in message.content.lower()
            else:
                return False
        except KeyError:
            return False

    async def learn(self, body: str) -> None:
        """thin wrapper for learn to switch to multiplex mode"""
        if self.settings['pyborg']['multiplex']:
            await self.aio_session.post(f"http://{self.multi_server}:{self.multi_port}/learn", data={"body": body}, raise_for_status=True)

    async def reply(self, body: str) -> Union[str, None]:
        """thin wrapper for reply to switch to multiplex mode: now coroutine"""
        if self.settings['pyborg']['multiplex']:
            url = f"http://{self.multi_server}:{self.multi_port}/reply"
            async with self.aio_session.post(url, data={"body": body}, raise_for_status=True) as ret:
                reply = await ret.text()
                logger.debug("got reply: %s", reply)
            return reply
        else:
            raise NotImplementedError

    async def teardown(self) -> None:
        "turn off the bot"
        await self.aio_session.close()

    def scan(self, module: ModuleType = builtin_commands) -> None:
        "look for commands to add to registry"
        self.scanner = venusian.Scanner(registry=self.registry)
        self.scanner.scan(module)


#class FancyCallable(Callable):
#    pass_msg: bool

class Registry():
    """Command registry of decorated pyborg commands"""
    def __init__(self, mod: PyborgDiscord) -> None:
        self.registered: Dict[str, Callable] = {}
        self.mod = mod

    def __str__(self):
        return f"{self.mod} command registry with {len(self.registered.keys())}"

    def add(self, name: str, ob: Callable, internals: bool, pass_msg: bool) -> None:
        "add command to the registry. takes two config options."
        self.registered[name] = ob
        if internals:
            self.registered[name] = partial(ob, self.mod.multiplexing, multi_server="http://{}:{}/".format(self.mod.multi_server, self.mod.multi_port))
            self.registered[name].pass_msg = False
        if pass_msg:
            self.registered[name].pass_msg = True
        else:
            self.registered[name].pass_msg = False
