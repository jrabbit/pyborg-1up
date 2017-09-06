import logging

import bottle
from bottle import request

from pyborg.util.bottle_plugin import BottledPyborg

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
    return pyborg.reply(body)



# @bottle.route("/save", method="POST")
# def reply(pyborg):
#     pyborg.save_brain()
#     return "OK"

# Advanced API

class DumbyIOMod(object):
    """fake IO mod for pyborg interop"""
    message = None
    def output(self, message, args):
        self.message = message
        self.args = args

@bottle.route("/process", method="POST")
def process(pyborg):
    body = request.POST.get("body")
    reply_rate = int(request.POST.get("reply_rate"))
    learning = request.POST.get("learning")
    owner = request.POST.get("owner")
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


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    bottle.install(BottledPyborg())
    bottle.run(host="localhost", port=2001, reloader=True)
