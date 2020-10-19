import logging
import os
import random
import shlex
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

import requests

logging.basicConfig(level=logging.DEBUG)
if sys.version_info >= (3,7):
    poetry_path = subprocess.run(["whereis", "-b", "poetry"], text=True, check=True, capture_output=True).stdout.split(":")[1]
    print(poetry_path)
else:
    poetry_path = subprocess.check_output(["whereis", "-b", "poetry"]).split(":")[1]

logging.info("poetry path: %s", poetry_path)
# class TestIntegrationRuns(unittest.TestCase):
    # def test_runs(self):
        # try:
            # port = random.randint(3000,5000)
            # self.run = subprocess.run(shlex.split(f"{poetry_path} run pyborg --debug http --port {port} --brain_name internal_test.pyborg.json"), timeout=3)
        # except subprocess.TimeoutExpired:
            # raise


class TestIntegratesFullServerReply(unittest.TestCase):
    def setUp(self):
        # self.tmp_f, self.tmp_path = tempfile.mkstemp()
        self.tmp_path = "internal_test.pyborg.json"
        self.port = random.randint(3000,5000)
        self.run = subprocess.Popen(shlex.split(f"{poetry_path} run pyborg --debug http --port {self.port} --brain_name {self.tmp_path}"))
        if os.getenv("CI", False):
            time.sleep(4)
        else:
            time.sleep(2)

    def test_learns(self):
        try:
            ret = requests.post(f"http://localhost:{self.port}/learn", data={"body": "pee pee"})
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_reply(self):
        try:
            ret = requests.post(f"http://localhost:{self.port}/reply", data={"body": "poo poo"})
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_save(self):
        try:
            ret = requests.post(f"http://localhost:{self.port}/save")
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()

    def test_stats(self):
        try:
            ret = requests.post(f"http://localhost:{self.port}/stats")
        except:
            print(self.run.stdout)
            self.run.kill()
            raise
        ret.raise_for_status()
        self.run.terminate()
