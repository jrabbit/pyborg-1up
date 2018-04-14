import logging
import os

import bottle
import six
import click
from bottle import request
from pyborg.util.bottle_plugin import BottledPyborg
from pyborg.util.stats import send_stats

logger = logging.getLogger(__name__)



@bottle.route("/")
def index(pyborg):
    return """<h1>Welcome to PyBorg/http</h1>
    <h2>{}</h2>
    <a href="/words.json">Words info (json)</a>""".format(pyborg.ver_string)

# Basic API

@bottle.route("/learn", method="POST")
def learn(pyborg):
    body = request.POST.getunicode("body")
    pyborg.learn(body)
    return "OK"


@bottle.route("/reply", method="POST")
def reply(pyborg):
    body = request.POST.getunicode("body")
    if six.PY2:
        body = body.decode("utf-8")
    logger.debug(type(body))
    return pyborg.reply(body)



@bottle.route("/save", method="POST")
def save(pyborg):
    pyborg.save_brain()
    return "Saved to {}".format(pyborg.brain_path)


@bottle.route("/info")
def info(pyborg):
    return pyborg.ver_string, pyborg.brain_path


@bottle.route("/stats", method="POST")
def stats(pyborg):
    "record stats to statsd"
    send_stats(pyborg)
    return "OK"

# Advanced API


class DumbyIOMod(object):

    """fake IO mod for pyborg interop"""

    commandlist = ""
    message = None
    def output(self, message, args):
        self.message = message
        self.args = args


@bottle.route("/process", method="POST")
def process(pyborg):
    body = request.POST.getunicode("body")
    if six.PY3:
        reply_rate = int(request.POST.get("reply_rate"))
    reply_rate = int(request.POST.get("reply_rate"))
    learning = int(request.POST.get("learning"))
    owner = int(request.POST.get("owner"))
    # logger.debug("process: type: owner: %s", type(owner))
    # logger.debug("process:body type: %s", type(body))
    # logger.debug("process:body: %s" ,body)

    io = DumbyIOMod()
    pyborg.process_msg(io, body, reply_rate, learning, None, owner)
    if io.message:
        return io.message
    return ""


@bottle.route("/known")
def known(pyborg):
    "return number of contexts"
    word = request.query.word
    try:
        c = len(pyborg.words[word])
        msg = "{} is known ({} contexts)".format(word, c)
        return msg
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


@bottle.route("/logging-level", method="POST")
def set_log_level():
    # when we drop 2 support this can use strings instead of the enums
    levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO,
              "WARNING": logging.WARNING, "ERROR": logging.ERROR, "CRITICAL": logging.CRITICAL}
    target = levels[request.POST.get("level").upper()]
    logger.setLevel(target)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    folder = click.get_app_dir("Pyborg")
    brain_path = os.path.join(folder, "brains", "current.pyborg.json")
    bottle.install(BottledPyborg(brain_path=brain_path))
    bottle.run(host="localhost", port=2001, reloader=True)
