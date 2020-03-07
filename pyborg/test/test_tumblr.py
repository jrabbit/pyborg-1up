import datetime
import json
import unittest
from pathlib import Path
from unittest import mock

import pyborg


class TestBot(unittest.TestCase):
    settings = {
        "auth": {"consumer_key": "KEY", "consumer_secret": "SECRET", "oauth_secret": "TOKEN", "oauth_token": "TOKEN",},
        "pyborg": {"multiplex": False},
        "tumblr": {
            "blog": "billoreilly.tumblr.com",
            "cooldown": 20,
            "ignore": [],
            "last_look": datetime.datetime(2016, 8, 18, 7, 25, 30, 164769),
            "learning": False,
            "tags": ["hello bill"],
        },
    }
    with open(Path(".", "pyborg", "test", "fixtures", "tumblr_posts.json")) as fixture_f:
        posts = json.load(fixture_f,)

    @mock.patch("pyborg.pyborg.pyborg")
    @mock.patch("pyborg.mod.mod_tumblr.logger.info")
    @mock.patch("pyborg.pyborg.pyborg.reply")
    @mock.patch("toml.load")
    def test_handle_post(self, patched_load, patched_pyborg, patched_info, pybpybpyb):
        patched_load.return_value = self.settings
        mod = pyborg.mod.mod_tumblr.PyborgTumblr("bogus.toml")

        # patched_new.return_value = {}
        # mod.start()
        mod.handle_post(self.posts[0])
        patched_load.assert_called_once_with("bogus.toml")
        patched_pyborg.return_value = "fuck it do it live"
        patched_info.assert_any_call("found post: \n%s", self.posts[0]["summary"])

    # print(patched_info.mock_calls)

    @mock.patch("pytumblr.TumblrRestClient.tagged")
    @mock.patch("pyborg.pyborg.pyborg")
    @mock.patch("toml.load")
    def test_load_new(self, patched_load, pybpybpyb, patched_tagged):
        patched_load.return_value = self.settings
        patched_tagged.return_value = self.posts
        mod = pyborg.mod.mod_tumblr.PyborgTumblr("bogus.toml")
        ret = mod.load_new_from_tag("hello bill")  # noqa: F841
        patched_tagged.assert_called_once_with("hello bill")

    # self.assertEqual(ret, )

    @mock.patch("time.sleep")
    @mock.patch("pyborg.mod.mod_tumblr.PyborgTumblr.load_new_from_tag")
    @mock.patch("pyborg.pyborg.pyborg")
    @mock.patch("toml.load")
    def test_start(self, patched_load, pybpybpyb, patched_new, patched_sleep):
        patched_load.return_value = self.settings
        mod = pyborg.mod.mod_tumblr.PyborgTumblr("bogus.toml")
        patched_sleep.side_effect = StopIteration
        with self.assertRaises(StopIteration):
            mod.start()
        patched_sleep.assert_called_once_with(self.settings["tumblr"]["cooldown"])

    @mock.patch("toml.dump")
    @mock.patch("pyborg.mod.mod_tumblr.open")
    @mock.patch("pyborg.pyborg.pyborg")
    @mock.patch("toml.load")
    def test_teardown(self, patched_load, pybpybpyb, patched_open, patched_dump):
        patched_load.return_value = self.settings
        mod = pyborg.mod.mod_tumblr.PyborgTumblr("bogus.toml")
        mod.teardown()
        patched_open.assert_called_once_with("bogus.toml", "w")
        # patched_dump.assert_called_once_with(self.settings, patched_open)
        print(patched_dump.mock_calls)
