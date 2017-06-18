import datetime
import json
import logging
import os
import pickle
import shutil
import sys
import zipfile

import click
import humanize
import pyborg
import pyborg.pyborg
import requests
import toml
from mastodon import Mastodon
from pyborg.mod.mod_irc import ModIRC
from pyborg.mod.mod_linein import ModLineIn
from pyborg.mod.mod_reddit import PyborgReddit
from pyborg.mod.mod_mastodon import PyborgMastodon

if sys.version_info <= (3,):
    from pyborg.mod.mod_tumblr import PyborgTumblr

if sys.version_info >= (3,):
    from pyborg.mod.mod_discord import PyborgDiscord

logger = logging.getLogger(__name__)

folder = click.get_app_dir("Pyborg")

def mk_folder():
    try:
        os.makedirs(os.path.join(folder, "brains"))
        logger.info("pyborg folder created.")
    except OSError:
        logger.info("pyborg folder already exists.")

@click.group()
@click.option('--debug', default=False, is_flag=True)
@click.option('--verbose/--silent', default=True)
def cli_base(verbose, debug):
    # only the first basicConfig() is respected.
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)

@cli_base.group()
def brain():
    "Pyborg brain (archive.zip) utils"
    pass

@brain.command("list")
def list_brains():
    "print out the pyborg brains (archive.zip)s info"
    print(os.path.join(folder,"brains") + ":")
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
        output  = os.path.join(folder, "brains", "{}.zip".format(backup_name))
    shutil.copy2(target, output)

@brain.command()
@click.argument('target_brain', default="current")
def stats(target_brain):
    "Get stats about a brain"
    if target_brain == "current":
        pyb = pyborg.pyborg.pyborg()
        print(json.dumps({"words": pyb.settings.num_words,
                "contexts": pyb.settings.num_contexts,
                "lines": len(pyb.lines)}))
    else:
        brain_path = os.path.join(folder, "brains", target_brain)
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
    output  = os.path.join(folder, "brains", "{}.zip".format(tag_name))
    shutil.copy2(target_brain, output)
    print("Imported your archive.zip as {}".format(output))

@brain.command("upgrade")
@click.argument('target_brain', default="current")
def upgrade_to_pickle(target_brain):
    "Upgrade from a version 1.2 pyborg brain to 1.3"
    try:
        os.makedirs(os.path.join(folder, "tmp"))
    except OSError:
        # Do nothing.
        pass
    if target_brain == "current":
        brain_path = "archive.zip"
    else:
        brain_path = os.path.join(folder, "brains", "{}.zip".format(target_brain))
    words, lines = pyborg.pyborg.pyborg.load_brain_2(brain_path)
    version = pyborg.pyborg.pyborg.saves_version
    # version = ???
    with open(os.path.join(folder, "tmp", "words.pkl"), 'wb') as w:
        pickle.dump(words, w)
    with open(os.path.join(folder, "tmp", "lines.pkl"), 'wb') as l:
        pickle.dump(lines, l)
    with open(os.path.join(folder, "tmp", "version.pkl"), 'wb') as v:
        pickle.dump(version, v)

    with zipfile.ZipFile("current.pybrain.zip", "w") as f:
        f.write(os.path.join(folder, "tmp",'words.pkl'), 'words.pkl')
        f.write(os.path.join(folder, "tmp",'lines.pkl'), 'lines.pkl')
        f.write(os.path.join(folder, "tmp",'version.pkl'), 'version.pkl')
    try:
        os.remove(os.path.join(folder, "tmp", 'words.pkl'))
        os.remove(os.path.join(folder, "tmp", 'lines.pkl'))
        os.remove(os.path.join(folder, "tmp", 'version.pkl'))
    except (OSError, IOError):
        logger.error("could not remove the files")


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
                        api_base_url = ctx.obj['base_url'],
                        to_file = cred_file)

@mastodon.command("login")
@click.argument("username")
@click.password_option()
@click.pass_context
@click.option("--cred-file", default='pyborg_mastodon_clientcred.secret', type=click.Path(exists=True))
def mastodon_login(ctx, cred_file, username, password):
    mastodon = Mastodon(client_id = cred_file,
                        api_base_url = ctx.obj['base_url'])
    mastodon.log_in(username,
                    password,
                    to_file = 'pyborg_mastodon_usercred.secret')


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
@click.option("--host", default="localhost")
@click.option("--port", default=2001)
@click.option("--reloader", default=False)
def http(reloader, port, host):
    "Run a server for mutliheaded (multiplex) pyborg"
    from pyborg.mod.mod_http import bottle, save
    bottle.run(host=host, port=port, reloader=reloader)
    save()

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




if __name__ == '__main__':
    # use this if we want to import third party commands or something
    # cli = click.CommandCollection(sources=[cli_base, brain])
    cli_base() # noqa
