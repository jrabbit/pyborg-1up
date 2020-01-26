import configparser
import logging
import os
import json
from typing import Optional

import click
import attr
import networkx as nx
import matplotlib.pyplot as plt
from networkx.readwrite import json_graph

logger = logging.getLogger(__name__)
folder = click.get_app_dir("Pyborg")


def mk_folder() -> None:
    try:
        os.makedirs(os.path.join(folder, "brains"))
        os.makedirs(os.path.join(folder, "tmp"))
        logger.info("pyborg folder created.")
    except OSError:
        logger.info("pyborg folder already exists.")

def networkx_demo(pyb, graphics=False, export=False):
    G = nx.Graph()
    print(pyb)

    G.add_node("fuck")

    for p in pyb.words["fuck"]:
        G.add_edge("fuck", pyb.lines[p["hashval"]][0])

    logger.info(G)

    if graphics:
        nx.draw(G)
        plt.show()
    if export:
        data = json_graph.node_link_data(G)
        s = json.dumps(data)
        return s


@attr.s
class Service:
    "a pyborg process a user may be running"
    name: str = attr.ib()
    desc: str = attr.ib()
    wants: str = attr.ib(default=False)

    def yeet(self, working_directory=None, user=True) -> None:
        "make a systemd unit file for this service"

        unit_file = f"pyborg_{self.name}.service"
        command = f"pyborg {self.name}"
        # configparser is ini
        config = configparser.ConfigParser()
        # we cant caps preserved
        # https://docs.python.org/3/library/configparser.html#configparser.ConfigParser.optionxform
        config.optionxform = lambda option: option # type: ignore
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
    Service("http", "pyborg multiplexing server"),
    Service("discord", "pyborg discord client", wants="pyborg_http"),
    Service("mastodon", "pyborg mastodon/activitypub client", wants="pyborg_http"),
    Service("twitter", "pyborg twitter client", wants="pyborg_http"),
    Service("tumblr", "pyborg tumblr client", wants="pyborg_http"),
]


def init_systemd() -> None:
    "pump out all unit files we know how"
    for service in SERVICES:
        service.yeet()
