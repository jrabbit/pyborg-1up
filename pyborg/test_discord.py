import sys
import unittest
import logging

try:
    from unittest import mock
except ImportError:
    import mock

if sys.version_info >= (3,):
    import asyncio

    import pyborg
    from pyborg.util.utils_testing import do_nothing

    logging.basicConfig(level=logging.INFO)

    class TestOnMessage(unittest.TestCase):
        def setUp(self):
           self.loop = asyncio.new_event_loop()
           asyncio.set_event_loop(self.loop)
        
        def tearDown(self):
            self.loop.close()

        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.user', create=True)
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.learn')
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.reply')
        def test_no_reply(self, patched_reply, patched_learn, patched_user):
            msg = mock.Mock()
            msg.content = "Yolo!"
            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/fixtures/discord.toml")
            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_reply.assert_not_called()
        
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.clean_msg')
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.user', create=True)
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.learn')
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.reply')
        def test_reply(self, patched_reply, patched_learn, patched_user, patched_clean):
            msg = mock.MagicMock()
            msg.content.return_value = "<@221134985560588289> you should play dota!"
            msg.channel.return_value = "maketotaldestroy"
            msg.author.mention.return_value = "<@42303631157544375>"

            patched_user.return_value.id = "221134985560588289"
            patched_reply.return_value = "I should play dota!"
            patched_reply.replace.return_value = "I should play dota!" 

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/fixtures/discord.toml")
            our_pybd.send_message = do_nothing
            
            self.loop.run_until_complete(our_pybd.on_message(msg))
            # print(our_pybd.user.id)
            # patched_user.id.assert_called_once_with()
            # print(patched_reply.mock_calls, patched_learn.mock_calls)
            # print(patched_send.mock_calls)
            patched_learn.assert_called_once_with(msg.content)
            patched_reply.assert_called_once_with(patched_clean.return_value)


        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.clean_msg')
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.user', create=True)
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.learn')
        @mock.patch('pyborg.mod.mod_discord.PyborgDiscord.reply')
        def test_nick_replace(self, patched_reply, patched_learn, patched_user, patched_clean):
            msg = mock.MagicMock()
            msg.content.return_value = "<@221134985560588289> you should play dota!"
            msg.channel.return_value = "maketotaldestroy"
            msg.author.mention.return_value = "<@42303631157544375>"

            patched_user.return_value.id = "221134985560588289"
            patched_reply.return_value = "I should play dota! #nick"
            patched_reply.replace.return_value = "I should play dota! <@42303631157544375>" 

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/fixtures/discord.toml")
            our_pybd.send_message = do_nothing
            
            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_learn.assert_called_once_with(msg.content)
            patched_reply.assert_called_once_with(patched_clean.return_value)
