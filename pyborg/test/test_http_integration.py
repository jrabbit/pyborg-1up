import logging
import shlex
import subprocess
import tempfile
import time
import unittest
from unittest import mock

import requests


logging.basicConfig(level=logging.DEBUG)

poetry_path = subprocess.run(["whereis", "-b", "poetry"], text=True, check=True, capture_output=True).stdout.split(":")[1]


class TestIntegrationRuns(unittest.TestCase):
    def test_runs(self):
        try:
            run = subprocess.run(shlex.split(f"{poetry_path} run pyborg --debug http --brain_name internal_test.pyborg.json"), timeout=3)
        except subprocess.TimeoutExpired:
            pass


class TestIntegratesFullServerReply(unittest.TestCase):
    def setUp(self):
        # self.tmp_f, self.tmp_path = tempfile.mkstemp()
        self.tmp_path = "internal_test.pyborg.json"
        self.run = subprocess.Popen(shlex.split(f"{poetry_path} run pyborg --debug http --brain_name {self.tmp_path}"))
        time.sleep(2)

    def test_learns(self):
        try:
            ret = requests.post("http://localhost:2001/learn", data={"body": "pee pee"})
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_reply(self):
        try:
            ret = requests.post("http://localhost:2001/reply", data={"body": "poo poo"})
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_save(self):
        try:
            ret = requests.post("http://localhost:2001/save")
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_stats(self):
        try:
            ret = requests.post("http://localhost:2001/stats")
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()
