import logging
import os
import sys
import tempfile
import unittest

import pyborg.pyborg

try:
    from unittest import mock
except ImportError:
    import mock

logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG)


class TestPyborgInit(unittest.TestCase):
    "Test all the pyborg loaders"

    blank_brain_path = "pyborg/test/fixtures/blank.brain.pyborg.json"
    old_style_brain = "pyborg/test/fixtures/old.brain.pyborg.archive.zip"
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    @mock.patch("pyborg.pyborg.pyborg.__init__")  # skip loading brain
    @mock.patch("toml.load")
    def test_load_settings(self, patched_toml, patched_init):
        patched_init.return_value = None
        our_pyb = pyborg.pyborg.pyborg()
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        ret = our_pyb.load_settings()
        expected_cfg = pyborg.pyborg.FakeCfg2(max_words=50000)
        self.assertEqual(ret, expected_cfg)

    # def test_load_brain_2(self):
    #   words, lines = pyborg.pyborg.pyborg.load_brain_2(self.old_style_brain)

    def test_load_brain_json_retuns_dicts(self):
        words, lines = pyborg.pyborg.pyborg.load_brain_json(
            self.blank_brain_path)
        self.assertIsInstance(words, dict)
        self.assertIsInstance(lines, dict)
        self.assertEqual(len(words), 0)
        self.assertEqual(len(lines), 0)

    def test_load_brain_json_loads_small(self):
        expected_lines = {713833202: ['destroy edgar', 1],
                          1071494628: ['murder edgar', 1],
                          2622503271: ['kill edgar', 2],
                          3025701897: ['fuck the moon', 1],
                          3127776909: ['fuck space', 1],
                          3710277035: ['are you a murderer', 1],
                          3953240527: ['fuck reddit', 1],
                          4186136012: ['fuck', 1]}

        expected_words = {'a': [{'hashval': 3710277035, 'index': 2}],
                          'are': [{'hashval': 3710277035, 'index': 0}],
                          'destroy': [{'hashval': 713833202, 'index': 0}],
                          'edgar': [{'hashval': 2622503271, 'index': 1},
                                    {'hashval': 713833202, 'index': 1},
                                    {'hashval': 1071494628, 'index': 1}],
                          'fuck': [{'hashval': 4186136012, 'index': 0},
                                   {'hashval': 3025701897, 'index': 0},
                                   {'hashval': 3127776909, 'index': 0},
                                   {'hashval': 3953240527, 'index': 0}],
                          'kill': [{'hashval': 2622503271, 'index': 0}],
                          'moon': [{'hashval': 3025701897, 'index': 2}],
                          'murder': [{'hashval': 1071494628, 'index': 0}],
                          'murderer': [{'hashval': 3710277035, 'index': 3}],
                          'reddit': [{'hashval': 3953240527, 'index': 1}],
                          'space': [{'hashval': 3127776909, 'index': 1}],
                          'the': [{'hashval': 3025701897, 'index': 1}],
                          'you': [{'hashval': 3710277035, 'index': 1}]}

        words, lines = pyborg.pyborg.pyborg.load_brain_json(self.small_brain)
        self.assertIsInstance(words, dict)
        self.assertIsInstance(lines, dict)
        self.assertEqual(len(words), 13)
        self.assertEqual(len(lines), 8)
        self.assertEqual(words, expected_words)
        self.assertEqual(lines, expected_lines)


class TestPyborgClobbersave(unittest.TestCase):

    def setUp(self):
        with open("archive.zip", "w") as archive:
            # touch the cat; do it stat!
            archive.write("")

    # @mock.patch('__main__.open', mock.mock_open()) 
    # this doesnt work????
    @mock.patch("toml.load")
    @mock.patch("pyborg.pyborg.pyborg.load_brain_json")
    def test_no_clobber(self, patched_load_brain, patched_toml):
        "sometimes 1.4 will nuke archive.zip"
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        patched_load_brain.side_effect = IOError
        our_pyb = pyborg.pyborg.pyborg()
        our_pyb.save_brain()

        with open("archive.zip") as archive:
            self.assertEqual(archive.read(), "")
        # patched_open.assert_called_once_with('foo', 'w')

class TestPyborgSave(unittest.TestCase):
    pass


class TestPyborgLearning(unittest.TestCase):
    "Test learning"
    @mock.patch("toml.load")
    def test_functional_learn(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain="/bogus/path")
        our_pyb.learn("Read a book, any book - Trotskist Proverb")
        our_pyb.learn("You should play dota 2 it's fun")
        our_pyb.learn("dota 2 is a free game")

        print("words:", our_pyb.words)
        print(our_pyb.settings.num_words)
        print(our_pyb)
        self.assertNotEqual(len(our_pyb.words), 0)


class TestPyborgReply(unittest.TestCase):
    blank_brain_path = "pyborg/test/fixtures/blank.brain.pyborg.json"
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    @mock.patch("toml.load")
    def test_no_reply(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.blank_brain_path)
        ret = our_pyb.reply("'Read a book, any book' - Trotskist Proverb")
        self.assertEqual(ret, "")

    @mock.patch("toml.load")
    def test_bs_reply(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        ret = our_pyb.reply("fuck")
        self.assertNotEqual(ret, "")
