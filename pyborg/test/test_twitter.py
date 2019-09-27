import unittest

try:
    from unittest import mock
except ImportError:
    import mock


class TestIgnoreImageTweets(unittest.TestCase):
    def test_ignore_blank_description(self):
        pass
