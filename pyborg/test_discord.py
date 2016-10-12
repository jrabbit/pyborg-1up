import sys
import unittest
import logging
import asyncio

try:
    from unittest import mock
except ImportError:
    import mock

if sys.version_info >= (3,):
    import pyborg_discord
    logging.basicConfig(level=logging.INFO)

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
        async def test_no_reply(self, patched_pyb_discord):
            msg = mock.Mock()
            msg.return_value.content = "Yolo!"
            our_pybd = pyborg_discord.PyborgDiscord("pyborg/fixtures/discord.toml")
            await our_pybd.on_message(msg)
            patched_pyb_discord.learn.assert_not_called()
        
        @mock.patch('pyborg_discord.PyborgDiscord.user', create=True)
        @mock.patch('pyborg_discord.PyborgDiscord.learn')
        @mock.patch('pyborg_discord.PyborgDiscord.reply')
        async def test_reply(self, patched_reply, patched_learn, patched_user):
            msg = mock.Mock()
            msg.content = "<@221134985560588289> you should play dota!"
            patched_user.return_value.id = "221134985560588289"
            our_pybd = pyborg_discord.PyborgDiscord("pyborg/fixtures/discord.toml")
            # loop = asyncio.get_event_loop()
            # loop.run_until_complete(our_pybd.on_message(msg))
            # loop.close()
            await our_pybd.on_message(msg)
            # print(our_pybd.user.id)
            # patched_pyb_discord.user.id.assert_called_once_with()
            print(patched_user.mock_calls, patched_user.mock_calls)
            print(msg.content)
            patched_learn.assert_called_once_with(msg.content)
            patched_reply.assert_called_once_with(msg.content)

