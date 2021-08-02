import logging
import os
import time
import tempfile
import unittest
from unittest import mock

from webtest import TestApp

from pyborg.mod.mod_http import bottle
from pyborg.mod import mod_http
from pyborg.util.bottle_plugin import BottledPyborg


logging.basicConfig(level=logging.DEBUG)


@mock.patch("nltk.word_tokenize")
@mock.patch("json.loads")
@mock.patch("builtins.open")
@mock.patch("toml.load", return_value={"pyborg-core": {"max_words": False}})
@mock.patch("pyborg.pyborg.pyborg.save_brain")
@mock.patch("pyborg.pyborg.pyborg.load_settings")
class TestIntegratesFullServerReply(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp_f, cls.tmp_path = tempfile.mkstemp()
        # start http server directly
        with mock.patch("toml.load", return_value={"pyborg-core": {"max_words": False}}) as _:
            bottle.install(BottledPyborg(brain_path=cls.tmp_path))
            bottle.debug(True)
            cls.app = TestApp(bottle.default_app())
        if os.getenv("CI", False):
            # let travis spin up sockets
            time.sleep(3)

    def test_learns(self, patched_settings, patched_brain, patched_toml, _, __, ___):
        ret = self.app.post("/learn", {"body": "pee pee"})
        # patched_settings.assert_called()

    def test_reply(self, patched_close, patched_toml, _, __, ___, ____):
        ret = self.app.post("/reply", {"body": "poo poo"})

    def test_save(self, patched_settings, patched_brain_save, patched_toml, _, ___, ____):
        ret = self.app.post("/save")
        patched_brain_save.assert_called_once()

    def test_stats(self, patched_closed, patched_toml, _, __, ___, ____):
        ret = self.app.post("/stats")
