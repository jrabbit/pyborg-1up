#!/usr/bin/env python

import asyncio
import collections
import datetime
import json
import logging
import os
import platform
import shutil
import struct
import sys
from pathlib import Path
from typing import Callable, Union

import click
import humanize
import requests
import six
import toml
import tweepy
from discord import Client, Guild
from mastodon import Mastodon

import pyborg
import pyborg.pyborg
from pyborg.mod.mod_discord import PyborgDiscord
from pyborg.mod.mod_filein import ModFileIn
from pyborg.mod.mod_http import bottle
from pyborg.mod.mod_irc import ModIRC
from pyborg.mod.mod_linein import ModLineIn
from pyborg.mod.mod_mastodon import PyborgMastodon
from pyborg.mod.mod_reddit import PyborgReddit
from pyborg.mod.mod_tumblr import PyborgTumblr
from pyborg.mod.mod_twitter import PyborgTwitter
from pyborg.util.bottle_plugin import BottledPyborg
from pyborg.util.config_defaults import configs as STOCK_CONFIGS
from pyborg.util.util_cli import init_systemd, mk_folder, networkx_demo

try:
    import aeidon
    from pyborg.mod.mod_subtitle import PyborgSubtitles
except ImportError:
    aeidon = False

try:
    import systemd.daemon
except ImportError:
    systemd = None



logger = logging.getLogger(__name__)


folder = click.get_app_dir("Pyborg")

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])


def resolve_brain(target_brain: str) -> str:
    "utility function to get the brain path"
    if target_brain == "current":
        brain_path = os.path.join(folder, "brains", "current.pyborg.json")

    elif os.path.exists(target_brain):
        brain_path = target_brain

    else:
        brain_path = os.path.join(folder, "brains", target_brain)
    logger.debug("Resolved brain: %s", brain_path)
    return brain_path


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.option("--version", "my_version", default=False, is_flag=True, help="output a version summary")
@click.option("--debug", default=False, is_flag=True, help="control log level")
@click.option("--verbose/--silent", default=True, help="control log level")
@click.pass_context
def cli_base(ctx: click.Context, verbose: bool, debug: bool, my_version: bool) -> None:
    """Pyborg is a markov chain bot for IRC
    (and other services [even at the same time with the same database])
    that generates replies based on messages and it’s database"""
    mk_folder()
    # only the first basicConfig() is respected.
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)
    if my_version:
        # Skip directly to version command like the user would expect a gnu program to.
        ctx.invoke(version)
        ctx.exit()
    elif ctx.invoked_subcommand is None:
        # still do normal things via the named help even
        ctx.invoke(local_help)


@cli_base.command("help")
@click.pass_context
def local_help(ctx: click.Context) -> None:
    """Show this message and exit."""
    print(ctx.parent.get_help())


@cli_base.command("folder")
def folder_info() -> None:
    "where pyborg will look for brains and toml confs"
    print(folder)
    logger.debug("folder: this uses https://click.palletsprojects.com/en/7.x/api/#click.get_app_dir and should work most of the time")


@cli_base.group()
def utils() -> None:
    "extra pyborg helper scripts"
    pass  # pylint: disable=W0107


@utils.command("http")
def dump_httpd_info() -> None:
    "http helper script"
    multi_protocol = "http"
    multi_server = "localhost"
    multi_port = 2001
    r = requests.get(f"{multi_protocol}://{multi_server}:{multi_port}/meta/status.json")
    r.raise_for_status()
    logging.debug(r)
    print(f"server is {'saving' if r.json()['status'] else 'not saving'}")

@utils.command("systemd")
def yeet_systemd() -> None:
    "put systemd unit files in current directory"
    print("generated systemd files are here in this directory. Copy them into systemd (try /usr/lib/systemd/system/) with any adjustments")
    print("for pyborg's http server:\n\tsudo install ./pyborg_http.service /usr/lib/systemd/system/")
    print("then run: \n\tsudo systemctl reload-daemon")
    init_systemd()


# Discord utils


@utils.group("manage-discord")
def discord_mgr() -> None:
    "run administrative tasks on the bot"
    pass  # pylint: disable=W0107


def _eris(f: Callable, debug: bool = False) -> None:
    "wrangle discord"
    conf = os.path.join(folder, "discord.toml")
    loop = asyncio.new_event_loop()
    # can we get the ctx/debug status?
    if debug:
        loop.set_debug(True)
    asyncio.set_event_loop(loop)
    our_discord_client = PyborgDiscord(conf, loop=loop)
    tasks = (our_discord_client.fancy_login(), asyncio.ensure_future(f(our_discord_client)), our_discord_client.teardown())
    t = asyncio.gather(*tasks, loop=loop)
    loop.run_until_complete(t)


@discord_mgr.command("ls")
def list_discord_servers() -> None:
    "list servers pyborg is on w/ an addressable hash or ID"

    async def list_inner(dc: Client) -> None:
        await asyncio.sleep(1)
        async for guild in dc.fetch_guilds(limit=100):
            try:
                print(guild, guild.id)
            except:
                logger.exception("manage-discord: had discord api issue probably")

    _eris(list_inner)


async def _resolve_guild(dc: Client, search_term: Union[int, str]) -> Guild:
    "internal utility method to get the guild by partial name or short id"
    for g in dc.guilds:
        print(g)
        if search_term.isdigit():
            if g.id == int(search_term):
                return g
        if g.id.startswith(search_term):
            return g
        if search_term in str(g):
            return g
    return False
    # raise BadDiscordServerFragement(search_term)


@discord_mgr.command("rm")
@click.argument("server_id_partial")
def leave_discord_server(server_id_partial: str) -> None:
    "leave server matching SERVER_ID_PARTIAL"

    async def leave_inner(dc: Client) -> None:
        await asyncio.sleep(1)
        guild_id = await _resolve_guild(dc, server_id_partial)
        logger.info("got %s", guild_id)
        if guild_id:
            g = await dc.fetch_guild(guild_id)
            if click.confirm(f"do you want to leave {g}?"):
                await g.leave()
        else:
            logger.error("manage-discord: Don't know what you meant?")

    _eris(leave_inner)


@discord_mgr.command("i-rm")
def interactive_leave_discord_server() -> None:
    "offers to leave servers one-by-one"

    async def leave_interactive_inner(dc: Client) -> None:
        await asyncio.sleep(1)
        async for guild in dc.fetch_guilds(limit=100):
            if click.confirm(f"do you want to leave {guild}?"):
                await guild.leave()
            else:
                print("ok, next...")

    _eris(leave_interactive_inner)


@discord_mgr.command("info")
@click.argument("server_id_partial")
def info_discord_server(server_id_partial: str) -> None:
    "basic stats, # of users, current nickname, public stuff."

    async def info_inner(dc: Client) -> None:
        await asyncio.sleep(1)
        g = await _resolve_guild(dc, server_id_partial)
        if g:
            print(g, g.id, g.me.display_name, g.member_count)
        else:
            logger.error("manage-discord: Didn't resolve a guild.")

    _eris(info_inner)


# Brains!


@cli_base.group()
def brain() -> None:
    "Pyborg brain (pybrain.json) utils"
    pass  # pylint: disable=W0107

@brain.command("ls")
@click.pass_context
def ls_brains(ctx) -> None:
    "shortcut for list"
    ctx.invoke(list_brains)


@brain.command("list")
def list_brains() -> None:
    "print out the pyborg brains (pybrain.json)s info"
    print(os.path.join(folder, "brains") + ":")
    for brain_name in os.listdir(os.path.join(folder, "brains")):
        brain_size = os.path.getsize(os.path.join(folder, "brains", brain_name))
        print("\t {0} {1}".format(brain_name, humanize.naturalsize(brain_size)))


@brain.command()
@click.option("--output", type=click.Path())
@click.argument("target_brain", default="current")
def backup(target_brain: str, output: str) -> None:
    "Backup a specific brain"
    target = resolve_brain(target_brain)
    backup_name = datetime.datetime.now().strftime("pyborg-%m-%d-%y-archive")
    if output is None:
        output = os.path.join(folder, "brains", "{}.zip".format(backup_name))
    shutil.copy2(target, output)


@brain.command()
@click.argument("target_brain", default="current")
def stats(target_brain: str) -> None:
    "Get stats about a brain"
    brain_path = resolve_brain(target_brain)
    pyb = pyborg.pyborg.pyborg(brain=brain_path)
    print(json.dumps({"words": pyb.settings.num_words, "contexts": pyb.settings.num_contexts, "lines": len(pyb.lines),}))

@brain.command()
@click.argument("target_brain", default="current")
def graph(target_brain: str) -> None:
    brain_path = resolve_brain(target_brain)
    pyb = pyborg.pyborg.pyborg(brain_path)
    print(networkx_demo(pyb, export=True))


@brain.command("import")
@click.argument("target_brain", type=click.Path(exists=True), default="archive.zip")
@click.option("--tag")
def convert(target_brain: str, tag: str) -> None:
    "move your brain to the new central location"
    mk_folder()
    if tag is None:
        tag_name = datetime.datetime.now().strftime("pyborg-%m-%d-%y-import-archive")
    else:
        tag_name = tag
    output = os.path.join(folder, "brains", "{}.zip".format(tag_name))
    shutil.copy2(target_brain, output)
    print("Imported your archive.zip as {}".format(output))


@brain.command("upgrade")
@click.argument("target_brain", default="current")
def upgrade_to_json(target_brain: str) -> None:
    "Upgrade from a version 1.2 pyborg brain to 1.4 mono-json dict format"
    if target_brain == "current":
        brain_path = "archive.zip"
    elif os.path.exists(target_brain):
        brain_path = target_brain
    else:
        brain_path = os.path.join(folder, "brains", "{}.zip".format(target_brain))
    words, lines = pyborg.pyborg.pyborg.load_brain_2(brain_path)
    version_str = "1.4.0"
    tag_name = datetime.datetime.now().strftime("%m-%d-%y-import-archive")
    save_path = os.path.join(folder, "brains", "{}.pyborg.json".format(tag_name))
    for key, value in words.items():
        if isinstance(key, six.text_type):
            logger.info("Repairing bad unicode type in dictionary...")
            del words[key]
            safe_key = key.encode("utf-8")
            logger.info("New type: %s", type(safe_key))
            logger.info("new key: %s", safe_key)
            words[safe_key] = value

    # Convert the structpacking to dicts

    for key, value in words.items():
        new_packed = []
        for packed in value:
            hashval, idx = struct.unpack("iH", packed)
            new_packed.append({"hashval": hashval, "index": idx})
        words[key] = new_packed

    with open(save_path, "wb") as brain_file:
        out = {"words": words, "lines": lines, "version": version_str}
        json.dump(out, brain_file)
    print("Wrote out pyborg brain into {}".format(save_path))


@brain.command()
@click.option("--one-two", is_flag=True)
@click.argument("target_brain", default="current")
def doctor(target_brain: str, one_two: bool) -> None:
    "run diagnostics on a specific pyborg brain"
    cnt = collections.Counter()
    brain_path = resolve_brain(target_brain)

    try:
        if one_two:
            words, lines = pyborg.pyborg.pyborg.load_brain_2(brain_path)
        else:
            words, lines = pyborg.pyborg.pyborg.load_brain_json(brain_path)

    except FileNotFoundError as e:
        logger.debug("brain not found", exc_info=e)
        print("we couldn't open that brain.")
        print("we looked in: {}".format(brain_path))
        sys.exit(8)

    # Type check the brain
    assert isinstance(words, dict)  # nosec
    assert isinstance(lines, dict)  # nosec
    for key, value in words.items():
        cnt[type(key)] += 1
        for i in value:
            cnt[type(i)] += 1
    # print(type(key))
    # for item in lines:
    #     cnt[type(item)] += 1
    print(cnt)


def check_server(server: str, port: int = 2001) -> None:
    "checks if the server is up or bails (exits)"
    try:
        response = requests.get(f"http://{server}:{port}/")
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        logger.error("pyborg http server uncontactable! exiting")
        sys.exit(8080)


def run_mastodon(conf_file: str, secret_folder: str) -> None:
    "run mastodon utility function"
    with open(conf_file) as f:
        settings = toml.load(f)
    try:
        check_server(settings["pyborg"]["multiplexing_server"])
    except KeyError:
        logger.error("toml file missing [pyborg][multiplexing_server] entry! exiting")
        sys.exit(78)

    bot = PyborgMastodon(toml_file=conf_file)
    try:
        bot.start(folder=secret_folder)
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise
@cli_base.command()
def yeet_config():
    for filename, settings in STOCK_CONFIGS:
        with open(Path(folder, filename)) as fd:
            toml.dump(fd, settings)
    print(f"put the files in {folder}")
            
@cli_base.group(invoke_without_command=True)
@click.pass_context
@click.option("--base-url", default="https://botsin.space/")
@click.option("--conf-file", default=os.path.join(folder, "mastodon.toml"))
@click.option("--secret-folder", default=folder)
def mastodon(ctx: click.Context, base_url: str, conf_file: str, secret_folder: str) -> None:
    "Run the mastodon mod; run register and login first"
    ctx.obj = dict()
    ctx.obj["base_url"] = base_url
    ctx.obj["secret_folder"] = secret_folder
    if ctx.invoked_subcommand is None:
        run_mastodon(conf_file, secret_folder)


@mastodon.command(name="register")
@click.argument("bot_name")
@click.pass_context
@click.option("--cred-file", default="pyborg_mastodon_clientcred.secret", type=click.Path())
def mastodon_register(ctx: click.Context, cred_file: str, bot_name: str) -> None:
    "register your bot's account on the homeserver"
    Mastodon.create_app(bot_name, api_base_url=ctx.obj["base_url"], to_file=os.path.join(ctx.obj["secret_folder"], cred_file))


@mastodon.command("login")
@click.argument("username")
@click.password_option()
@click.pass_context
@click.option(
    "--cred-file", default="pyborg_mastodon_clientcred.secret", type=click.Path(exists=True),
)
def mastodon_login(ctx: click.Context, cred_file: str, username: str, password: str) -> None:
    "login to your homeserver"
    masto = Mastodon(client_id=cred_file, api_base_url=ctx.obj["base_url"])
    masto.log_in(username, password, to_file=os.path.join(ctx.obj["secret_folder"], "pyborg_mastodon_usercred.secret"))


@cli_base.command()
@click.option("--conf-file", type=click.Path(), default=os.path.join(folder, "irc.toml"))
def irc(conf_file: str) -> None:
    "runs the irc2 module a slim, secure pyborg irc bot"
    pyb = pyborg.pyborg.pyborg
    settings = toml.load(conf_file)
    if settings["multiplex"]:
        try:
            check_server(settings["multiplex_server"])
        except requests.exceptions.ConnectionError:
            logger.error("Connection to pyborg server failed!")
            print("Is pyborg_http running?")
            sys.exit(2)

    bot = ModIRC(pyb, settings)
    bot.scan(module=pyborg.commands)
    logging.debug("Command Registry: %s", bot.registry.registered)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.teardown()
        bot.disconnect("Killed at terminal.")
    except IOError as e:
        if bot.settings["multiplex"]:
            logger.error(e)
            logger.info("Is pyborg http running?")
        else:
            raise

    except Exception as e:
        logger.exception(e)
        bot.teardown()
        bot.disconnect("Caught exception")
        raise e


@cli_base.command()
@click.option("--conf-file", type=click.Path(), default=os.path.join(folder, "tumblr.toml"))
def tumblr(conf_file: str) -> None:
    "watch a tumblr tag for posts to respond to"

    bot = PyborgTumblr(conf_file)

    try:
        bot.start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.command()
@click.option("--brain_name", default="current")
@click.option("--host", default="localhost")
@click.option("--port", default=2001)
@click.option("--reloader", default=False)
def http(reloader: bool, port: int, host: str, brain_name: str) -> None:
    "Run a server for mutliheaded (multiplex) pyborg"
    brain_path = resolve_brain(brain_name)
    if systemd:
        logger.info("booting with systemd notify support")
        bottle.install(BottledPyborg(brain_path=brain_path, notify=True))
    else:
        bottle.install(BottledPyborg(brain_path=brain_path))
    bottle.run(host=host, port=port, reloader=reloader)
    bottle.default_app().close()


@cli_base.command("set-log-level")
@click.argument("log-level")
def set_logging_level(log_level: str) -> None:
    """configure mod_http's log level after launch

    use the levels from `logging`: (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    ret = requests.post("http://localhost:2001/logging-level", data={"level": log_level})
    ret.raise_for_status()


if aeidon:

    @cli_base.command()
    @click.argument("subtitle-file")
    @click.option("--conf-file", default=os.path.join(folder, "subtitle.toml"))
    def subtitles(conf_file: str, subtitle_file: str) -> None:
        "learn from subtitles! python3 only! thx aeidon"
        subs = PyborgSubtitles(conf_file=conf_file, subs_file=subtitle_file)
        subs.start()


@cli_base.command()
@click.option("--conf-file", default=os.path.join(folder, "twitter.toml"))
def twitter(conf_file: str) -> None:
    "be your own horse_ebooks: twitter module"

    mod = PyborgTwitter(conf_file)
    try:
        mod.start()
    except KeyboardInterrupt:
        mod.teardown()
        sys.exit()
    except Exception:
        mod.teardown()
        raise


def get_api(conf_file: str) -> tweepy.API:
    "get twitter api utility function"

    twsettings = toml.load(conf_file)
    auth = tweepy.OAuthHandler(twsettings["twitter"]["auth"]["consumer_key"], twsettings["twitter"]["auth"]["consumer_secret"],)
    auth.set_access_token(
        twsettings["twitter"]["auth"]["access_token"], twsettings["twitter"]["auth"]["access_token_secret"],
    )
    api = tweepy.API(auth)
    return api


@cli_base.command()
@click.argument("target-user")
@click.option("--conf-file", default=os.path.join(folder, "twitter.toml"))
def follow_twitter_user(conf_file: str, target_user: str) -> None:
    "follow a twitter user over the api"
    api = get_api(conf_file)
    api.create_friendship(target_user)


# @cli_base.command()
# @click.option("--conf-file", default=os.path.join(folder, "twitter.toml"))
# def twitter_debug_shell(conf_file):
#     api = get_api(conf_file)
#     from IPython import embed
#     embed()


@cli_base.command()
@click.argument("input-file")
@click.option("--multiplex", default=True, type=click.BOOL)
def filein(multiplex: bool, input_file: str) -> None:
    """ascii file input module"""

    mod = ModFileIn(multiplexing=multiplex)
    mod.run(input_file)


@cli_base.command()
@click.option("--conf-file", default=os.path.join(folder, "discord.toml"))
def discord(conf_file: str) -> None:
    "Run the discord client"
    bot = PyborgDiscord(toml_file=conf_file)
    try:
        bot.our_start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.command()
@click.option("--conf-file", default="reddit.toml")
def reddit(conf_file: str) -> None:
    "Runs the reddit module"
    bot = PyborgReddit(conf_file)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.command()
@click.option("--multiplex", default=True, type=click.BOOL)
def linein(multiplex: bool) -> None:
    "This is a commandline repl for interacting with pyborg locally"
    my_pyborg = pyborg.pyborg.pyborg
    try:
        mod = ModLineIn(my_pyborg, multiplex)
    except SystemExit:
        if not multiplex:
            mod.save()
        raise


@cli_base.command()
def version() -> None:
    "output a version summary"
    print("I am a version {} pyborg!".format(pyborg.__version__))
    print("I'm running on {} {}/{}".format(platform.python_implementation(), platform.python_version(), platform.platform(),))


if __name__ == "__main__":
    # use this if we want to import third party commands or something
    # cli = click.CommandCollection(sources=[cli_base, brain])
    cli_base()  # noqa pylint: disable=E1120
