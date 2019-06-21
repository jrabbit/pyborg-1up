import logging
import unittest
import os

import pyborg.pyborg
from pyborg.mod.mod_http import DumbyIOMod

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

    @mock.patch("pyborg.pyborg.open", mock.mock_open())
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

    @mock.patch("toml.load")
    @mock.patch("pyborg.pyborg.pyborg.load_brain_json")
    def test_no_clobber(self, patched_load_brain, patched_toml, ):
        "sometimes 1.4 will nuke archive.zip"
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        patched_load_brain.side_effect = IOError
        our_pyb = pyborg.pyborg.pyborg()
        if os.path.exists("archive.zip"):
            with open("archive.zip") as archive:
                self.assertEqual(archive.read(), "")
        self.assertNotEqual(our_pyb.brain_path, "archive.zip")


class TestPyborgSave(unittest.TestCase):
    blank_brain_path = "pyborg/test/fixtures/blank.brain.pyborg.json"

    lines = {713833202: ['destroy edgar', 1],
             1071494628: ['murder edgar', 1],
             2622503271: ['kill edgar', 2],
             3025701897: ['fuck the moon', 1],
             3127776909: ['fuck space', 1],
             3710277035: ['are you a murderer', 1],
             3953240527: ['fuck reddit', 1],
             4186136012: ['fuck', 1]}

    words = {'a': [{'hashval': 3710277035, 'index': 2}],
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

    @mock.patch("os.rename")
    @mock.patch("pyborg.pyborg.open", mock.mock_open())
    @mock.patch("json.loads")
    @mock.patch("toml.load")
    def test_save_db(self, patched_toml, patched_json, patched_rename):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        patched_json.return_value = {'version': u"1.4.0", 'words': self.words, 'lines': self.lines}
        our_pyb = pyborg.pyborg.pyborg(brain="/bogus/path")
        # our_pyb.brain_path = ""
        our_pyb.save_brain()
        # print(m.mock_calls)


class TestPyborgLearning(unittest.TestCase):
    "Test learning"

    @mock.patch("pyborg.pyborg.pyborg.load_brain_json")
    @mock.patch("toml.load")
    def test_functional_learn(self, patched_toml, patched_load):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        patched_load.return_value = (dict(), dict())
        our_pyb = pyborg.pyborg.pyborg(brain="/bogus/path")
        our_pyb.learn("Read a book, any book - Trotskist Proverb")
        our_pyb.learn("You should play dota 2 it's fun")
        our_pyb.learn("dota 2 is a free game")

        print("words:", our_pyb.words)
        print(our_pyb.settings.num_words)
        print(our_pyb)
        self.assertNotEqual(len(our_pyb.words), 0)


@mock.patch("toml.load")
class TestPyborgUnlearnWord(unittest.TestCase):
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    def test_unlearn_unknown_small(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.unlearn("Romania")

    def test_unlearn_known_linked_small(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.unlearn("edgar")
        self.assertNotIn("edgar", our_pyb.words)

    def test_unlearn_known_leaf_small(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.unlearn("the")
        self.assertNotIn("the", our_pyb.words)


@mock.patch("toml.load", return_value={"pyborg-core": {"max_words": False}})
class TestPyborgPurgeWord(unittest.TestCase):
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    def test_purge_word_command(self, patched_toml):
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        iomod = DumbyIOMod()
        msg = "!purge"
        our_pyb.process_msg(iomod, msg, 0, True, None, 1)
        print(iomod.messages)


class TestPyborgFilterWord(unittest.TestCase):
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    @mock.patch("toml.load")
    def test_censored_reply(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.settings.censored = ["murder"]
        ret = our_pyb.reply("murder")
        self.assertEqual(ret, "")

    @mock.patch("toml.load")
    def test_censored_reply_regex(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.settings.censored = ["murder"]
        ret = our_pyb.reply("murderer")
        self.assertEqual(ret, "")
        ret2 = our_pyb.reply("murder")
        self.assertEqual(ret2, "")
        ret3 = our_pyb.reply("murderize")
        self.assertEqual(ret3, "")


class TestPyborgIsFiltered(unittest.TestCase):
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    def test_is_filter_regex(self):
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        our_pyb.settings.censored = ["fuck"]
        self.assertTrue(our_pyb._is_censored("fuck"))
        self.assertFalse(our_pyb._is_censored("hello"))
        self.assertTrue(our_pyb._is_censored("fucker"))


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

    @mock.patch("toml.load")
    def test_unicode_reply(self, patched_toml):
        patched_toml.return_value = {"pyborg-core": {"max_words": False}}
        our_pyb = pyborg.pyborg.pyborg(brain=self.small_brain)
        ret = our_pyb.reply("fuck \U0001f52b")
        print(ret)
