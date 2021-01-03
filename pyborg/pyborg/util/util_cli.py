import configparser
import logging
import os
from typing import Optional

import click
import attr

logger = logging.getLogger(__name__)
folder = click.get_app_dir("Pyborg")


def mk_folder() -> None:
    "create pyborg folders."
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
    wants: Optional[str] = attr.ib(default=None)
    service_type: str = attr.ib(default="simple")

    def yeet(self, working_directory=None, user=True) -> None:
        "make a systemd unit file for this service"

        unit_file = f"pyborg_{self.name}.service"
        command = f"pyborg {self.name}"
        # configparser is ini
        config = configparser.ConfigParser()
        # we cant caps preserved
        # https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
        config.optionxform = lambda option: option  # type: ignore
        config["Unit"] = dict()
        config["Unit"]["Description"] = self.desc
        config["Unit"]["Documentation"] = "https://pyborg.readthedocs.io/en/latest/deploy.html"
        config["Unit"]["After"] = "network.target"
        if self.wants:
            config["Unit"]["Wants"] = self.wants
        startline = f"poetry run {command}"
        config["Service"] = dict()
        config["Service"]["ExecStart"] = startline
        config["Service"]["ExecReload"] = "/bin/kill -HUP $MAINPID"
        config["Service"]["KillMode"] = "process"
        config["Service"]["SyslogIdentifier"] = f"pyborg_f{self.name}"
        config["Service"]["Environment"] = "PYTHONUNBUFFERED=1"
        if working_directory:
            config["Service"]["WordkingDirectory"] = working_directory
        config["Service"]["Restart"] = "on-failure"
        if user:
            config["Service"]["User"] = "pyborg"
        config["Install"] = dict()
        config["Install"]["WantedBy"] = "multi-user.target"

        with open(unit_file, "w") as fp:
            config.write(fp)


@attr.s
class Timer:
    name: str = attr.ib()


SERVICES = [
    Service("http", "pyborg multiplexing server", service_type="notify"),
    Service("discord", "pyborg discord client", wants="pyborg_http"),
    Service("mastodon", "pyborg mastodon/activitypub client", wants="pyborg_http"),
    Service("twitter", "pyborg twitter client", wants="pyborg_http"),
    Service("tumblr", "pyborg tumblr client", wants="pyborg_http"),
]


def init_systemd() -> None:
    "pump out all unit files we know how"
    for service in SERVICES:
        service.yeet()
