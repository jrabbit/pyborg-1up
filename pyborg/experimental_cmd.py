import logging
import sys

import click
import toml
import requests
import pyborg
import pyborg.pyborg
from pyborg.mod.mod_irc import ModIRC
from pyborg.mod.mod_http import bottle, save

logger = logging.getLogger(__name__)


@click.group()
@click.option('--debug', default=False)
@click.option('--verbose/--silent', default=True)
def cli_base(verbose, debug):
    # only the first basicConfig() is respected.
    if debug:
        logging.basicConfig(level=logging.DEBUG)
    if verbose:
        logging.basicConfig(level=logging.INFO)

def check_server():
    response = requests.get("http://localhost:2001/")
    response.raise_for_status()

@cli_base.command()
@click.option("--conf-file", default="example.irc.toml")
def irc(conf_file):
    pyb = pyborg.pyborg.pyborg
    settings = toml.load(conf_file)
    if settings['multiplex']:
        try:
            check_server()
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
            logger.info("Is pyborg_http running?")
        else:
            raise
    except Exception as e:
        logger.exception(e)
        bot.teardown()
        bot.disconnect("Caught exception")
        raise e


@cli_base.command()
@click.option("--reloader", default=False)
def http(reloader):
    bottle.run(host="localhost", port=2001, reloader=reloader)
    save()



if __name__ == '__main__':
    # cli = click.CommandCollection(sources=[cli_base])
    cli_base()