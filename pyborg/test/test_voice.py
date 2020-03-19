import logging
import sys
import unittest

from unittest import mock
from functools import partial
import asyncio

import asynctest

import pyborg
from pyborg.util.utils_testing import do_nothing

class TestVoiceConnect(unittest.TestCase):

    def test_generate(self):
        pass


class TestVoiceChannelChooser(unittest.TestCase):
    def setUp(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")

    def tearDown(self):
        self.loop.close()

    def test_one_user(self):
        mock_guild = mock.MagicMock()
        ch1 = mock.MagicMock()
        ch1.members.return_value = ["person1", "person2"]
        ch2 = mock.MagicMock()
        ch2.members.return_value = []
        mock_guild.voice_channels = [ch1, ch2]
        pybd = pyborg.mod.mod_discord.PyborgDiscord("pyborg/test/fixtures/discord.toml")
        pref_channel = pybd._vc_with_people(mock_guild)
        self.assertEqual(pref_channel, ch1)
