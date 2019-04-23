#!/usr/bin/env python

import collections
import datetime
import json
import logging
import platform
import shutil
import struct
import sys
import os

import click
import humanize
import pyborg
import pyborg.pyborg
import requests
import six
import toml
from mastodon import Mastodon
from pyborg.mod.mod_http import bottle
from pyborg.mod.mod_irc import ModIRC
from pyborg.mod.mod_linein import ModLineIn
from pyborg.mod.mod_reddit import PyborgReddit
from pyborg.util.bottle_plugin import BottledPyborg
from pyborg.util.util_cli import mk_folder

if sys.version_info <= (3,):
    from pyborg.mod.mod_tumblr import PyborgTumblr

if sys.version_info >= (3,):
    from pyborg.mod.mod_mastodon import PyborgMastodon
    from pyborg.mod.mod_subtitle import PyborgSubtitles
    from pyborg.mod.mod_discord import PyborgDiscord

logger = logging.getLogger(__name__)

folder = click.get_app_dir("Pyborg")

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


def resolve_brain(target_brain):
    if target_brain == "current":
        brain_path = os.path.join(folder, "brains", "current.pyborg.json")

    elif os.path.exists(target_brain):
        brain_path = target_brain

    else:
        brain_path = os.path.join(folder, "brains", target_brain)
    logger.debug("Resolved brain: %s", brain_path)
    return brain_path


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', default=False, is_flag=True)
@click.option('--verbose/--silent', default=True)
def cli_base(verbose, debug):
    mk_folder()
    # only the first basicConfig() is respected.
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)


@cli_base.command()
@click.pass_context
def help(ctx):
    """Show this message and exit."""
    print(ctx.parent.get_help())


@cli_base.command("folder")
def folder_info():
    "where pyborg will look for brains and toml confs"
    print(folder)
    logger.debug("folder: this uses https://click.palletsprojects.com/en/7.x/api/#click.get_app_dir and should work most of the time")


@cli_base.group()
def brain():
    "Pyborg brain (pybrain.json) utils"
    pass


@brain.command("list")
def list_brains():
    "print out the pyborg brains (pybrain.json)s info"
    print(os.path.join(folder, "brains") + ":")
    for x in os.listdir(os.path.join(folder, "brains")):
        brain_size = os.path.getsize(os.path.join(folder, "brains", x))
        print("\t {0} {1}".format(x, humanize.naturalsize(brain_size)))


@brain.command()
@click.option('--output', type=click.Path())
@click.argument('target_brain', default="current")
def backup(target_brain, output):
    "Backup a specific brain"
    if target_brain == "current":
        target = os.path.join(folder, "brains", "archive.zip")
    backup_name = datetime.datetime.now().strftime("pyborg-%m-%d-%y-archive")
    if output is None:
        output = os.path.join(folder, "brains", "{}.zip".format(backup_name))
    shutil.copy2(target, output)


@brain.command()
@click.argument('target_brain', default="current")
def stats(target_brain):
    "Get stats about a brain"
    brain_path = resolve_brain(target_brain)
    pyb = pyborg.pyborg.pyborg(brain=brain_path)
    print(
        json.dumps(
            {
                "words": pyb.settings.num_words,
                "contexts": pyb.settings.num_contexts,
                "lines": len(pyb.lines),
            }
        )
    )


@brain.command("import")
@click.argument('target_brain', type=click.Path(exists=True), default="archive.zip")
@click.option('--tag')
def convert(target_brain, tag):
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
@click.argument('target_brain', default="current")
def upgrade_to_json(target_brain):
    "Upgrade from a version 1.2 pyborg brain to 1.4 mono-json dict format"
    if target_brain == "current":
        brain_path = "archive.zip"
    elif os.path.exists(target_brain):
        brain_path = target_brain
    else:
        brain_path = os.path.join(folder, "brains", "{}.zip".format(target_brain))
    words, lines = pyborg.pyborg.pyborg.load_brain_2(brain_path)
    version = u"1.4.0"
    tag_name = datetime.datetime.now().strftime("%m-%d-%y-import-archive")
    save_path = os.path.join(folder, "brains", "{}.pyborg.json".format(tag_name))
    for key, value in words.items():
        if isinstance(key, six.text_type):
            logger.info("Repairing bad unicode type in dictionary...")
            del words[key]
            safe_key = key.encode('utf-8')
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

    with open(save_path, 'wb') as brain_file:
        out = {"words": words, "lines": lines, "version": version}
        json.dump(out, brain_file)
    print("Wrote out pyborg brain into {}".format(save_path))


@brain.command()
@click.option('--one-two', is_flag=True)
@click.argument('target_brain', default="current")
def doctor(target_brain, one_two):
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
    assert isinstance(words, dict)
    assert isinstance(lines, dict)
    for key, value in words.items():
        cnt[type(key)] += 1
        for i in value:
            cnt[type(i)] += 1
    # print(type(key))
    # for item in lines:
    #     cnt[type(item)] += 1
    print(cnt)


def check_server(server):
    response = requests.get("http://{}:2001/".format(server))
    response.raise_for_status()


def run_mastodon(conf_file, secret_folder):
    bot = PyborgMastodon(conf_file)
    try:
        bot.start(folder=secret_folder)
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.group(invoke_without_command=True)
@click.pass_context
@click.option("--base-url", default='https://mastodon.social')
@click.option("--conf-file", default=os.path.join(folder, "pyborg.mastodon.toml"))
@click.option("--secret-folder", default=folder)
def mastodon(ctx, base_url, conf_file, secret_folder):
    "Run the mastodon mod; run register and login first"
    ctx.obj = dict()
    ctx.obj['base_url'] = base_url
    ctx.obj['secret_folder'] = secret_folder
    if ctx.invoked_subcommand is None:
        run_mastodon(conf_file, secret_folder)


@mastodon.command(name="register")
@click.argument("bot_name")
@click.pass_context
@click.option(
    "--cred-file", default='pyborg_mastodon_clientcred.secret', type=click.Path()
)
def mastodon_register(ctx, cred_file, bot_name):
    Mastodon.create_app(bot_name, api_base_url=ctx.obj['base_url'], to_file=os.path.join(ctx.obj['secret_folder'], cred_file))


@mastodon.command("login")
@click.argument("username")
@click.password_option()
@click.pass_context
@click.option(
    "--cred-file",
    default='pyborg_mastodon_clientcred.secret',
    type=click.Path(exists=True),
)
def mastodon_login(ctx, cred_file, username, password):
    mastodon = Mastodon(client_id=cred_file, api_base_url=ctx.obj['base_url'])
    mastodon.log_in(username, password, to_file=os.path.join(ctx.obj['secret_folder'], 'pyborg_mastodon_usercred.secret'))


@cli_base.command()
@click.option("--conf-file", type=click.Path(), default=os.path.join(folder, "irc.toml"))
def irc(conf_file):
    "runs the irc2 module a slim, secure pyborg irc bot"
    pyb = pyborg.pyborg.pyborg
    settings = toml.load(conf_file)
    if settings['multiplex']:
        try:
            check_server(settings['multiplex_server'])
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
        if bot.settings['multiplex']:
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
@click.option("--conf-file", type=click.Path(), default=os.path.join(folder, "example.tumblr.toml"))
def tumblr(conf_file):
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
@click.option("--brain", default="current")
@click.option("--host", default="localhost")
@click.option("--port", default=2001)
@click.option("--reloader", default=False)
def http(reloader, port, host, brain):
    "Run a server for mutliheaded (multiplex) pyborg"
    brain_path = resolve_brain(brain)
    bottle.install(BottledPyborg(brain_path=brain_path))
    bottle.run(host=host, port=port, reloader=reloader)
    bottle.default_app().close()


@cli_base.command('set-log-level')
@click.argument("log-level")
def set_logging_level(log_level):
    """configure mod_http's log level after launch

    use the levels from `logging`: (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    ret = requests.post(
        "http://localhost:2001/logging-level", data={"level": log_level}
    )
    ret.raise_for_status()


@cli_base.command()
@click.argument("subtitle-file")
@click.option("--conf-file", default=os.path.join(folder, "subtitle.toml"))
def subtitles(conf_file, subtitle_file):
    "learn from subtitles! python3 only! thx aeidon"
    subs = PyborgSubtitles(conf_file=conf_file, subs_file=subtitle_file)
    subs.start()


@cli_base.command()
@click.option("--conf-file", default=os.path.join(folder, "pyborg.twitter.toml"))
def twitter(conf_file):
    from pyborg.mod.mod_twitter import PyborgTwitter

    mod = PyborgTwitter(conf_file)
    try:
        mod.start()
    except KeyboardInterrupt:
        mod.teardown()
        sys.exit()
    except Exception:
        mod.teardown()
        raise


def get_api(conf_file):
    import tweepy

    twsettings = toml.load(conf_file)
    auth = tweepy.OAuthHandler(
        twsettings['twitter']['auth']['consumer_key'],
        twsettings['twitter']['auth']['consumer_secret'],
    )
    auth.set_access_token(
        twsettings['twitter']['auth']['access_token'],
        twsettings['twitter']['auth']['access_token_secret'],
    )
    api = tweepy.API(auth)
    return api


@cli_base.command()
@click.argument("target-user")
@click.option("--conf-file", default=os.path.join(folder, "pyborg.twitter.toml"))
def follow_twitter_user(conf_file, target_user):
    "follow a twitter user over the api"
    api = get_api(conf_file)
    api.create_friendship(target_user)


# @cli_base.command()
# @click.option("--conf-file", default=os.path.join(folder, "pyborg.twitter.toml"))
# def twitter_debug_shell(conf_file):
#     api = get_api(conf_file)
#     from IPython import embed
#     embed()


@cli_base.command()
@click.argument("input-file")
@click.option("--multiplex", default=True, type=click.BOOL)
def filein(multiplex, input_file):
    """ascii file input module"""
    from pyborg.mod.mod_filein import ModFileIn

    mod = ModFileIn(multiplexing=multiplex)
    mod.run(input_file)


@cli_base.command()
@click.option("--conf-file", default=os.path.join(folder, "pyborg.discord.toml"))
def discord(conf_file):
    "Run the discord client (needs python3)"
    if sys.version_info <= (3,):
        print(
            "You are trying to run the discord mod under python 2. \nThis won't work. Please use python 3 (3.6+)."
        )
        sys.exit(6)
    bot = PyborgDiscord(conf_file)
    try:
        bot.our_start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.command()
@click.option("--conf-file", default="pyborg.reddit.toml")
def reddit(conf_file):
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
def linein(multiplex):
    "This is a commandline repl for interacting with pyborg locally"

    my_pyborg = pyborg.pyborg.pyborg
    try:
        mod = ModLineIn(my_pyborg, multiplex)
    except SystemExit:
        pass
    if not multiplex:
        mod.save()


@cli_base.command()
def version():
    print("I am a version {} pyborg!".format(pyborg.__version__))
    print(
        "I'm running on {} {}/{}".format(
            platform.python_implementation(),
            platform.python_version(),
            platform.platform(),
        )
    )


if __name__ == '__main__':
    # use this if we want to import third party commands or something
    # cli = click.CommandCollection(sources=[cli_base, brain])
    cli_base()  # noqa
