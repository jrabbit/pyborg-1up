import unittest
import json
import logging
import sys


if sys.version_info >= (3,):
    from unittest import mock
    from pyborg.mod.mod_mastodon import PyborgMastodon

    logging.basicConfig(level=logging.DEBUG)

    @mock.patch("pyborg.mod.mod_mastodon.PyborgMastodon.should_reply_direct")
    @mock.patch("pyborg.mod.mod_mastodon.PyborgMastodon.learn")
    @mock.patch("pyborg.mod.mod_mastodon.PyborgMastodon.reply")
    @mock.patch("mastodon.Mastodon.status_post")
    class TestTimezoneCrap(unittest.TestCase):

        with open("pyborg/test/fixtures/toots.json") as f:
            toots = json.load(f)
        conf_file = "pyborg/test/fixtures/pyborg.mastodon.toml"

        def test_time_compare(self, patched_post, patched_reply, patched_learn, patched_should):
            patched_should.return_value = True
            m = PyborgMastodon(self.conf_file)
            m.my_id = '9052'
            m.mastodon = mock.patch("mastodon.Mastodon")
            m.mastodon.status_post = mock.MagicMock()
            m.handle_toots(self.toots)
