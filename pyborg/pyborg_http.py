import bottle
import baker
from bottle import request
from pyborg.pyborg import pyborg

our_pyborg = pyborg()


@bottle.route("/learn", method="POST")
def learn():
    body = request.POST.get("body")
    our_pyborg.learn(body)
    return "OK"


@bottle.route("/reply", method="POST")
def reply():
    body = request.POST.get("body")
    return our_pyborg.reply(body)


@bottle.route("/")
def index():
    return "<h1>Welcome to Pyborg/http</h1>"

if __name__ == '__main__':
    bottle.run(host="localhost", port=2001, reloader=True)
