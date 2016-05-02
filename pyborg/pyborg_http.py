import bottle
import baker
from bottle import request
from pyborg.pyborg import pyborg

our_pyborg = pyborg()


@bottle.route("/")
def index():
    return "<h1>Welcome to Pyborg/http</h1>"

# Basic API

@bottle.route("/learn", method="POST")
def learn():
    body = request.POST.get("body")
    our_pyborg.learn(body)
    return "OK"


@bottle.route("/reply", method="POST")
def reply():
    body = request.POST.get("body")
    return our_pyborg.reply(body)


# Advanced API

class DumbyIOMod(object):
    message = None
    """fake IO mod for pyborg interop"""
    def output(self, message, args):
        self.message = message
        self.args = args

@bottle.route("/process", method="POST")
def process():
    body = request.POST.get("body")
    reply_rate = request.POST.get("reply_rate")
    learning = request.POST.get("learning")
    owner = request.POST.get("owner")
    io = DumbyIOMod()
    our_pyborg.process_msg(io, body, reply_rate, learning, None, owner)
    if io.message:
        return io.message
    else:
        return ""

if __name__ == '__main__':
    bottle.run(host="localhost", port=2001, reloader=True)
    our_pyborg.save_all()
