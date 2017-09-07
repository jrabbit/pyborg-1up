#!/usr/bin/env python

import collections
import datetime
import json
import logging
import os
import platform
import shutil
import struct
import sys

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
from pyborg.mod.mod_mastodon import PyborgMastodon
from pyborg.mod.mod_reddit import PyborgReddit
from pyborg.util.bottle_plugin import BottledPyborg
from pyborg.util.util_cli import mk_folder

if sys.version_info <= (3,):
    from pyborg.mod.mod_tumblr import PyborgTumblr

if sys.version_info >= (3,):
    from pyborg.mod.mod_subtitle import PyborgSubtitles
    from pyborg.mod.mod_discord import PyborgDiscord

logger = logging.getLogger(__name__)

folder = click.get_app_dir("Pyborg")




def resolve_brain(target_brain):
    if target_brain == "current":
        brain_path = os.path.join(folder, "brains", "current.pyborg.json")

    elif os.path.exists(target_brain):
        brain_path = target_brain

    else:
        brain_path = os.path.join(folder, "brains", target_brain)
    logger.debug("Resolved brain: %s", brain_path)
    return brain_path

@click.group()
@click.option('--debug', default=False, is_flag=True)
@click.option('--verbose/--silent', default=True)
def cli_base(verbose, debug):
    mk_folder()
    # only the first basicConfig() is respected.
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)


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
    print(json.dumps({"words": pyb.settings.num_words,
                      "contexts": pyb.settings.num_contexts,
                      "lines": len(pyb.lines)}))


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
        brain_path = os.path.join(
            folder, "brains", "{}.zip".format(target_brain))
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
        out = {"words": words,
               "lines": lines,
               "version": version}
        json.dump(out, brain_file)
    print("Wrote out pyborg brain into {}".format(save_path))


@brain.command()
@click.option('--one-two', is_flag=True)
@click.argument('target_brain', default="current")
def doctor(target_brain, one_two):
    cnt = collections.Counter()

    brain_path = resolve_brain(target_brain)

    if one_two:
        words, lines = pyborg.pyborg.pyborg.load_brain_2(brain_path)
    else:
        words, lines = pyborg.pyborg.pyborg.load_brain_json(brain_path)

    # Type check the brain
    assert isinstance(words, dict)
    assert isinstance(lines, dict)
    for key, value in words.items():
        cnt[type(key)] += 1
        # cnt[type(value)] += 1
        for i in value:
            cnt[type(i)] += 1
        # print(type(key))
    # for item in lines:
    #     cnt[type(item)] += 1
    print(cnt)


def check_server(server):
    response = requests.get("http://{}:2001/".format(server))
    response.raise_for_status()


def run_mastodon(conf_file):
    bot = PyborgMastodon(conf_file)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise


@cli_base.group(invoke_without_command=True)
@click.pass_context
@click.option("--base-url", default='https://mastodon.social')
@click.option("--conf-file", default="pyborg.mastodon.toml")
def mastodon(ctx, base_url, conf_file):
    "Run the mastodon mod; run register and login first"
    ctx.obj = dict()
    ctx.obj['base_url'] = base_url
    if ctx.invoked_subcommand is None:
        run_mastodon(conf_file)


@mastodon.command(name="register")
@click.argument("bot_name")
@click.pass_context
@click.option("--cred-file", default='pyborg_mastodon_clientcred.secret', type=click.Path())
def mastodon_register(ctx, cred_file, bot_name):
    Mastodon.create_app(bot_name,
                        api_base_url=ctx.obj['base_url'],
                        to_file=cred_file)


@mastodon.command("login")
@click.argument("username")
@click.password_option()
@click.pass_context
@click.option("--cred-file", default='pyborg_mastodon_clientcred.secret', type=click.Path(exists=True))
def mastodon_login(ctx, cred_file, username, password):
    mastodon = Mastodon(client_id=cred_file,
                        api_base_url=ctx.obj['base_url'])
    mastodon.log_in(username,
                    password,
                    to_file='pyborg_mastodon_usercred.secret')


@cli_base.command()
@click.option("--conf-file", default="example.irc.toml")
def irc(conf_file):
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
@click.option("--conf-file", default="example.tumblr.toml")
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


@cli_base.command()
@click.argument("subtitle-file")
@click.option("--conf-file", default=os.path.join(folder, "subtitle.toml"))
def subtitles(conf_file, subtitle_file):
    subs = PyborgSubtitles(conf_file=conf_file, subs_file=subtitle_file)
    subs.start()




@cli_base.command()
@click.option("--conf-file", default="example.discord.toml")
def discord(conf_file):
    "Run the discord client (needs python3)"
    if sys.version_info <= (3,):
        print("You are trying to run the discord mod under python 2. \nThis won't work. Please use python 3.")
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
    print("I'm running on {} {}/{}".format(platform.python_implementation(),
                                           platform.python_version(), platform.platform()))


if __name__ == '__main__':
    # use this if we want to import third party commands or something
    # cli = click.CommandCollection(sources=[cli_base, brain])
    cli_base()  # noqa
