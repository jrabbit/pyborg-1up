import logging
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

    @mock.patch("pyborg.pyborg.pyborg.__init__") # skip loading brain
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
        words, lines = pyborg.pyborg.pyborg.load_brain_json(self.blank_brain_path)
        self.assertIsInstance(words, dict)
        self.assertIsInstance(lines, dict)
        self.assertEqual(len(words), 0)
        self.assertEqual(len(lines), 0)


class TestPyborgLearning(unittest.TestCase):
    "Test learning"
    def test_functional_learn(self):
        our_pyb = pyborg.pyborg.pyborg(brain="/bogus/path")
        our_pyb.learn("'Read a book, any book' - Trotskist Proverb")
        print("words:", our_pyb.words)
        self.assertNotEqual(len(our_pyb.words), 0)
        print(our_pyb.settings.num_words)
        print(our_pyb)


class TestPyborgReply(unittest.TestCase):
    blank_brain_path = "pyborg/test/fixtures/blank.brain.pyborg.json"
    small_brain = "pyborg/test/fixtures/small.brain.pyborg.json"

    def test_no_reply(self):
        our_pyb = pyborg.pyborg.pyborg(brain=self.blank_brain_path)
        ret = our_pyb.reply("'Read a book, any book' - Trotskist Proverb")
        self.assertEqual(ret, "")
