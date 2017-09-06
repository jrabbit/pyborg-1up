import sys
import unittest
import logging

try:
    from unittest import mock
except ImportError:
    import mock

import pyborg.pyborg


logger = logging.getLogger(__name__)

# logging.basicConfig(level=logging.DEBUG)

class TestPyborgInit(unittest.TestCase):
	"Test all the pyborg loaders"

	@mock.patch("pyborg.pyborg.__init__")
	@mock.patch("toml.load")
	def test_load_settings(self, patched_toml, patched_init):
		our_pyb = pyborg.pyborg.pyborg()
		patched_toml.return_value = {"pyborg-core": {"max_words": False}}
		ret = our_pyb.load_settings()
		expected_cfg = pyborg.pyborg.FakeCfg2(max_words=50000)
		self.assertEqual(ret, expected_cfg)

