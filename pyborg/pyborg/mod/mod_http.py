import logging

import bottle
import six
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
    body = request.POST.get("body")
    pyborg.learn(body)
    return "OK"


@bottle.route("/reply", method="POST")
def reply(pyborg):
    body = request.POST.get("body")
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
    body = request.POST.get("body")
    if six.PY3:
        reply_rate = int(request.POST.get("reply_rate"))
    reply_rate = int(request.POST.get("reply_rate"))
    learning = int(request.POST.get("learning"))
    owner = int(request.POST.get("owner"))
    # logger.debug("process: type: owner: %s", type(owner))
    io = DumbyIOMod()
    pyborg.process_msg(io, body, reply_rate, learning, None, owner)
    if io.message:
        return io.message
    return ""

@bottle.route("/words.json")
def words_json(pyborg):
    return {"words": pyborg.settings.num_words,
            "contexts": pyborg.settings.num_contexts,
            "lines": len(pyborg.lines)}

@bottle.route("/commands.json")
def commands_json(pyborg):
    return pyborg.commanddict

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bottle.install(BottledPyborg())
    bottle.run(host="localhost", port=2001, reloader=True)
