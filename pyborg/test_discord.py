import sys
import unittest

try:
    from unittest import mock
except ImportError:
    import mock

if sys.version_info >= (3,):
    import pyborg_discord
    class TestLaunch(unittest.TestCase):
        @mock.patch('pyborg_discord.PyborgDiscord')
        def test_launch(self, patched_pyb_discord):
            pyborg_discord.start_discord_bot()
            patched_pyb_discord.assert_called_with('example.discord.toml')
            patched_pyb_discord.return_value.our_start.assert_called_with()

        @mock.patch('sys.exit')
        @mock.patch('pyborg_discord.PyborgDiscord')
        def test_ctrl_c(self, patched_pyb_discord, patched_exit):
            patched_pyb_discord.return_value.our_start.side_effect = KeyboardInterrupt()
            # with self.assertRaises(KeyboardInterrupt):
            pyborg_discord.start_discord_bot()
            patched_exit.assert_called_once_with()
            patched_pyb_discord.return_value.teardown.assert_called_once_with()


        @mock.patch('pyborg_discord.PyborgDiscord')
        def test_handle_exception(self, patched_pyb_discord):
            patched_pyb_discord.return_value.our_start.side_effect = Exception
            with self.assertRaises(Exception):
                pyborg_discord.start_discord_bot()
            patched_pyb_discord.return_value.teardown.assert_called_once_with()

    class TestOnMessage(unittest.TestCase):
        @mock.patch('pyborg_discord.PyborgDiscord')
        def test_no_reply(self, patched_pyb_discord):
            msg = mock.Mock()
            msg.return_value.content = "Yolo!"
            our_pybd = pyborg_discord.PyborgDiscord("afake.toml")
            our_pybd.on_message(msg)
            patched_pyb_discord.learn.assert_not_called()
        
        @mock.patch('pyborg_discord.PyborgDiscord')
        def test_reply(self, patched_pyb_discord):
            pass
            
