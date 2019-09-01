import unittest

from unittest import mock
import pyborg


@unittest.skip("2019 - This breaks green(weirdly it's probably the sys.exit)/ aren't very good tests.")
class TestLaunch(unittest.TestCase):
    @mock.patch('pyborg.mod.mod_reddit.PyborgReddit')
    def test_launch(self, patched_pyb_reddit):
        reddit = pyborg.mod.mod_reddit.PyborgReddit()
        reddit.start()
        patched_pyb_reddit.assert_called_with('pyborg.reddit.toml')
        patched_pyb_reddit.return_value.start.assert_called_with()

    @mock.patch('sys.exit')
    @mock.patch('pyborg.mod.mod_reddit.PyborgReddit')
    def test_ctrl_c(self, patched_pyb_reddit, patched_exit):
        patched_pyb_reddit.return_value.start.side_effect = KeyboardInterrupt()
        # with self.assertRaises(KeyboardInterrupt):
        reddit = pyborg.mod.mod_reddit.PyborgReddit()
        reddit.start()
        patched_exit.assert_called_once_with()

    @mock.patch('pyborg.mod.mod_reddit.PyborgReddit')
    def test_handle_exception(self, patched_pyb_reddit):
        patched_pyb_reddit.return_value.start.side_effect = Exception
        reddit = pyborg.mod.mod_reddit.PyborgReddit()
        with self.assertRaises(Exception):
            reddit.start()
