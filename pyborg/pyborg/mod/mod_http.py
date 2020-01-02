"""
pyborg http server for multiplexing backend/brain access
"""

import logging
import os
from pathlib import Path
from typing import List

import bottle
import click
from bottle import request
from filelock import FileLock

from pyborg.util.bottle_plugin import BottledPyborg
from pyborg.util.stats import send_stats

logger = logging.getLogger(__name__)
folder = click.get_app_dir("Pyborg")
SAVE_LOCK = FileLock(Path(folder, ".pyborg_is_saving.lock"))


@bottle.route("/")
def index(pyborg):
    return f"""<html><h1>Welcome to PyBorg/http</h1>
    <h2>{pyborg.ver_string}</h2>
    <a href='/words.json'>Words info (json)</a>
    <h2>Is the db saving?</h2>
    <p>{SAVE_LOCK.is_locked}</p>
    </html>"""

# Basic API


@bottle.route("/learn", method="POST")
def learn(pyborg):
    body = request.POST.getunicode("body")
    pyborg.learn(body)
    return "OK"


@bottle.route("/reply", method="POST")
def reply(pyborg):
    body = request.POST.getunicode("body")
    logger.debug(type(body))
    return pyborg.reply(body)


@bottle.route("/save", method="POST")
def save(pyborg):
    with SAVE_LOCK:
        pyborg.save_brain()
        return f"Saved to {pyborg.brain_path}"


@bottle.route("/info")
def info(pyborg):
    return pyborg.ver_string, pyborg.brain_path


@bottle.route("/info.json")
def info2(pyborg):
    return {"version_string": pyborg.ver_string, "brain": pyborg.brain_path}


@bottle.route("/stats", method="POST")
def stats(pyborg):
    "record stats to statsd"
    send_stats(pyborg)
    return "OK"

# Advanced API


class DumbyIOMod:
    """fake IO mod for pyborg interop"""
    def __init__(self):
        self.commandlist = ""
        self.message = None
        self.messages: List[str] = []  # New for multi-line output
        self.args = None

    def output(self, message, args):
        self.messages.append(message)
        self.message = message
        self.args = args


@bottle.route("/process", method="POST")
def process(pyborg):
    body = request.POST.getunicode("body")
    reply_rate = int(request.POST.get("reply_rate"))
    learning = int(request.POST.get("learning"))
    owner = int(request.POST.get("owner"))
    # logger.debug("process: type: owner: %s", type(owner))
    # logger.debug("process:body type: %s", type(body))
    # logger.debug("process:body: %s" ,body)

    fake_io = DumbyIOMod()
    pyborg.process_msg(fake_io, body, reply_rate, learning, None, owner)
    if fake_io.message:
        return fake_io.message
    return ""


@bottle.route("/known")
def known(pyborg):
    "return number of contexts"
    word = request.query.word
    try:
        return f"{word} is known ({len(pyborg.words[word])} contexts)"
    except KeyError:
        return "word not known"


@bottle.route("/words.json")
def words_json(pyborg):
    return {"words": pyborg.settings.num_words,
            "contexts": pyborg.settings.num_contexts,
            "lines": len(pyborg.lines)}


@bottle.route("/commands.json")
def commands_json(pyborg):
    return pyborg.commanddict


@bottle.get("/meta/status.json")
def save_lock_status(pyborg):
    return {"status": SAVE_LOCK.is_locked}


@bottle.post("/meta/logging-level")
def set_log_level():
    """levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO,
              "WARNING": logging.WARNING, "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
    """
    logger.setLevel(request.POST.get("level").upper())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    folder = click.get_app_dir("Pyborg")
    bottle.install(BottledPyborg(brain_path=os.path.join(folder, "brains", "current.pyborg.json")))
    bottle.run(host="localhost", port=2001, reloader=True)
