import logging
import os
import time
import tempfile
import unittest
from unittest import mock

from webtest import TestApp

from pyborg.mod.mod_http import bottle
from pyborg.util.bottle_plugin import BottledPyborg


logging.basicConfig(level=logging.DEBUG)


@mock.patch("toml.load", return_value={"pyborg-core": {"max_words": False}})
@mock.patch("pyborg.pyborg.pyborg.save_brain")
class TestIntegratesFullServerReply(unittest.TestCase):
    def setUp(self):
        self.tmp_f, self.tmp_path = tempfile.mkstemp()
        # start http server directly
        bottle.install(BottledPyborg(brain_path=self.tmp_path))
        app = bottle.default_app()
        self.app = TestApp(app)

    def test_learns(self, patched_close, patched_toml):
        ret = self.app.post("/learn", {"body": "pee pee"})

    def test_reply(self, patched_close, patched_toml):
        ret = self.app.post("/reply", {"body": "poo poo"})

    def test_save(self, patched_close, patched_toml):
        ret = self.app.post("/save")

    def test_stats(self, patched_closed, patched_toml):
        ret = self.app.post("/stats")
