import configparser
import logging
import os
from typing import Optional

import click
import attr

logger = logging.getLogger(__name__)
folder = click.get_app_dir("Pyborg")


def mk_folder() -> None:
    try:
        os.makedirs(os.path.join(folder, "brains"))
        os.makedirs(os.path.join(folder, "tmp"))
        logger.info("pyborg folder created.")
    except OSError:
        logger.info("pyborg folder already exists.")


@attr.s
class Service:
    "a pyborg process a user may be running"
    name: str = attr.ib()
    desc: str = attr.ib()

    def yeet(self, working_directory=None, user=True) -> None:
        "make a systemd unit file for this service"

        unit_file = f"pyborg_{self.name}.service"
        command = f"pyborg {self.name}"
        # configparser is ini
        config = configparser.ConfigParser()
        # we cant caps preserved
        # https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
        config.optionxform = lambda option: option
        config["Unit"] = dict()
        config["Unit"]["Description"] = self.desc
        config["Unit"]["After"] = "network.target"
        startline = f"poetry run {command}"
        config["Service"] = dict()
        config["Service"]["ExecStart"] = startline
        config["Service"]["ExecReload"] = "/bin/kill -HUP $MAINPID"
        config["Service"]["KillMode"] = "process"

        if working_directory:
            config["Service"]["WordkingDirectory"] = working_directory

        config["Service"]["Restart"] = "on-failure"
        if user:
            config["Service"]["User"] = "pyborg"
        config["Install"] = dict()
        config["Install"]["WantedBy"] = "multi-user.target"

        with open(unit_file, "w") as fp:
            config.write(fp)

SERVICES = [
    Service("http", "pyborg multiplexing server"),
    Service("discord", "pyborg discord client"),
    Service("mastodon", "pyborg mastodon/activitypub client"),
    Service("twitter", "pyborg twitter client"),
    Service("tumblr", "pyborg tumblr client"),
]


def init_systemd() -> None:
    "pump out all unit files we know how"
    for service in SERVICES:
        service.yeet()
