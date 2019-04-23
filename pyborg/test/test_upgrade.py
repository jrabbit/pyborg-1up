import logging
import unittest

try:
    from unittest import mock
except ImportError:
    import mock
from click.testing import CliRunner

from pyborg_entrypoint import upgrade_to_json

logger = logging.getLogger(__name__)

class TestUpgrade1_4(unittest.TestCase):
    "test upgrade from 1.2 to 1.4"

    @classmethod
    def setUpClass(cls):
        cls.click_runner = CliRunner()

    @mock.patch("json.dump")
    @mock.patch("pyborg.pyborg.pyborg.load_brain_2")
    def test_upgrade_to_json(self, patched_load, patched_dump):
        "test the cli command to upgrade to 1.4"
        patched_load.return_value = [{}, {}]
        result = self.click_runner.invoke(upgrade_to_json, ["/bozo_path.json"], catch_exceptions=False)
        self.assertEqual(result.exit_code, 0, msg=result)
        print(result)
