import logging
import sys
import unittest

if sys.version_info >= (3,):
    from unittest import mock
    from functools import partial
    import asyncio

    import asynctest
    
    import pyborg
    from pyborg.util.utils_testing import do_nothing

    logging.basicConfig(level=logging.DEBUG)

    class TestOnMessage(unittest.TestCase):
        def setUp(self):
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            #self.loop.set_debug(True)

        def tearDown(self):
            self.loop.close()

        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.user", create=True)
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.learn")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.reply")
        def test_no_reply(self, patched_reply, patched_learn, patched_user):
            msg = mock.Mock()
            msg.content = "Yolo!"
            patched_reply.return_value = ""
            patched_user.mentioned_in.return_value = False
            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")

            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_reply.assert_not_called()

        @mock.patch("pyborg.mod.mod_discord.normalize_awoos")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.user", create=True)
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.learn")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.reply")
        def test_reply(self, patched_reply, patched_learn, patched_user, patched_normalize):
            msg = asynctest.MagicMock()
            msg.content.return_value = "<@221134985560588289> you should play dota!"
            msg.content.split.return_value = ["<@!221134985560588289>", "you", "should", "play", "dota!"]
            msg.channel.return_value = "maketotaldestroy"
            msg.author.mention.return_value = "<@42303631157544375>"
            msg.channel.send = asynctest.CoroutineMock()
            patched_user.return_value.id = "221134985560588289"
            patched_reply.return_value = "I should play dota!"
            patched_reply.replace.return_value = "I should play dota!"

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")
            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_learn.assert_called_once_with(patched_normalize.return_value)
            patched_reply.assert_called_once_with(patched_normalize.return_value)

        @mock.patch("pyborg.mod.mod_discord.normalize_awoos")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.user", create=True)
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.learn")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.reply")
        def test_nick_replace(self, patched_reply, patched_learn, patched_user, patched_normalize):
            msg = asynctest.MagicMock()
            msg.content.return_value = "<@221134985560588289> you should play dota!"
            msg.content.split.return_value = ["<@!221134985560588289>", "you", "should", "play", "dota!"]
            msg.channel.return_value = "maketotaldestroy"
            msg.channel.send = asynctest.CoroutineMock()
            msg.author.mention.return_value = "<@42303631157544375>"

            patched_user.return_value.id = "221134985560588289"
            patched_reply.return_value = "I should play dota! #nick"
            patched_reply.replace.return_value = "I should play dota! <@42303631157544375>"

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")
            our_pybd.send_message = do_nothing
            our_pybd.send_typing = partial(do_nothing, "bogus_arg")

            self.loop.run_until_complete(our_pybd.on_message(msg))
            # print(asyncio.Task.all_tasks())
            patched_learn.assert_called_once_with(patched_normalize.return_value)
            patched_reply.assert_called_once_with(patched_normalize.return_value)

    @unittest.skip
    class TestCustomEmojis(unittest.TestCase):
        def setUp(self):
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            # self.loop.set_debug(True)

        def tearDown(self):
            self.loop.close()

        @mock.patch("pyborg.mod.mod_discord.normalize_awoos")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.user", create=True)
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.learn")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.reply")
        def test_learn_custom_emojis(self, patched_reply, patched_learn, patched_user, patched_normalize):
            msg = mock.MagicMock()
            original = "attempt <:weedminion:392111795642433556> replacement"
            content = mock.MagicMock()
            content.return_value = original
            msg.content = content
            msg.content.__contains__.return_value = True
            msg.content.split.return_value = ["attempt", "<:weedminion:392111795642433556>", "replacement"]
            msg.content.partition.return_value = ("attempt ", "<:weedminion:392111795642433556>", " replacement")
            msg.channel.return_value = "maketotaldestroy"
            # patched_normalize.return_value = 'attempt <:weedminion:392111795642433556> replacement'
            expected = "attempt weedminion replacement"

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")
            our_pybd.send_message = do_nothing
            our_pybd.send_typing = partial(do_nothing, "bogus_arg")

            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_normalize.assert_called_once_with(expected)

            patched_learn.assert_called_once_with(expected)
            patched_reply.assert_called_once_with(original)

        @mock.patch("pyborg.mod.mod_discord.normalize_awoos")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.user", create=True)
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.learn")
        @mock.patch("pyborg.mod.mod_discord.PyborgDiscord.reply")
        def test_learn_custom_emojis_simple(self, patched_reply, patched_learn, patched_user, patched_normalize):
            msg = mock.MagicMock()
            original = "<:weedminion:392111795642433556>"
            content = mock.MagicMock()
            content.return_value = original
            msg.content = content
            msg.content.__contains__.return_value = True
            msg.content.split.return_value = ["<:weedminion:392111795642433556>"]
            msg.content.partition.return_value = ("attempt ", "<:weedminion:392111795642433556>", " replacement")
            msg.channel.return_value = "maketotaldestroy"
            expected = "weedminion"

            our_pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")
            our_pybd.send_message = do_nothing
            our_pybd.send_typing = partial(do_nothing, "bogus_arg")

            self.loop.run_until_complete(our_pybd.on_message(msg))
            patched_normalize.assert_called_once_with(expected)
            # patched_learn.assert_called_once_with(expected)
            patched_reply.assert_called_once_with(original)

        def test_extract_emoji(self):
            from pyborg.mod.mod_discord import PyborgDiscord

            msg = mock.MagicMock()
            original = "<:weedminion:392111795642433556>"
            content = mock.MagicMock()
            content.return_value = original
            msg.content.partition.return_value = ("", "<:weedminion:392111795642433556>", "")
            msg.content = content
            our_pybd = PyborgDiscord("pyborg/test/fixtures/discord.toml")
            extracted = our_pybd._extract_emoji(msg, ["weedminion"])
            self.assertEqual(extracted, "weedminion")
