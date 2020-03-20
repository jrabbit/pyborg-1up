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
    config = attr.ib(factory=configparser.ConfigParser)

    def yeet(self, working_directory=None, user=True) -> None:
        "make a systemd unit file for this service"

        unit_file = f"pyborg_{self.name}.service"
        command = f"pyborg {self.name}"
        # configparser is ini
        # we cant caps preserved
        # https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
        self.config.optionxform = lambda option: option  # type: ignore
        self.config["Unit"] = dict()
        self.config["Unit"]["Description"] = self.desc
        self.config["Unit"]["Documentation"] = "https://pyborg.readthedocs.io/en/latest/deploy.html"
        self.config["Unit"]["After"] = "network.target"
        if self.wants:
            self.config["Unit"]["Wants"] = self.wants
        startline = f"poetry run {command}"
        self.config["Service"] = dict()
        self.config["Service"]["ExecStart"] = startline
        self.config["Service"]["ExecReload"] = "/bin/kill -HUP $MAINPID"
        self.config["Service"]["KillMode"] = "process"
        self.config["Service"]["SyslogIdentifier"] = f"pyborg_f{self.name}"
        self.config["Service"]["Environment"] = "PYTHONUNBUFFERED=1"
        if working_directory:
            self.config["Service"]["WordkingDirectory"] = working_directory
        self.config["Service"]["Restart"] = "on-failure"
        if user:
            self.config["Service"]["User"] = "pyborg"
        self.config["Install"] = dict()
        self.config["Install"]["WantedBy"] = "multi-user.target"

        with open(unit_file, "w") as fp:
            self.config.write(fp)


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
