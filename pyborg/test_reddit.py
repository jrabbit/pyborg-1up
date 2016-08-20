import unittest
import mock

import pyborg_reddit

class TestLaunch(unittest.TestCase):
    @mock.patch('pyborg_reddit.PyborgReddit')
    def test_launch(self, patched_pyb_reddit):
        pyborg_reddit.start_reddit_bot()
        patched_pyb_reddit.assert_called_with('pyborg.reddit.toml')
        patched_pyb_reddit.return_value.start.assert_called_with()

    @mock.patch('sys.exit')
    @mock.patch('pyborg_reddit.PyborgReddit')
    def test_ctrl_c(self, patched_pyb_reddit, patched_exit):
        patched_pyb_reddit.return_value.start.side_effect = KeyboardInterrupt()
        # with self.assertRaises(KeyboardInterrupt):
        pyborg_reddit.start_reddit_bot()
        patched_exit.assert_called_once_with()

    @mock.patch('pyborg_reddit.PyborgReddit')
    def test_handle_exception(self, patched_pyb_reddit):
        patched_pyb_reddit.return_value.start.side_effect = Exception
        with self.assertRaises(Exception):
            pyborg_reddit.start_reddit_bot()