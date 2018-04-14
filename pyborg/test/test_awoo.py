import sys
import unittest
import logging

try:
    from unittest import mock
except ImportError:
    import mock

from pyborg.util.awoo import normalize_awoos


class TestAwooNormalize(unittest.TestCase):

    def test_1_awoo(self):
        out = normalize_awoos("awooooooo")
        self.assertEqual(out, "awoo")

    def test_2_awoo(self):
        out = normalize_awoos("awooooooo awoooooooooooooooo")
        self.assertEqual(out, "awoo awoo")

    def test_real_world(self):
        out = normalize_awoos("real awooooo hours who up?")
        self.assertEqual(out, "real awoo hours who up?")

    def test_uppercase_awoo(self):
        out = normalize_awoos("real AWOOOOOOOO hours who up?")
        self.assertEqual(out, "real awoo hours who up?")

    def test_mixed_awoo(self):
        out = normalize_awoos("real Awoooooo hours who up?")
        self.assertEqual(out, "real awoo hours who up?")
