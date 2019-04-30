import logging
import json
import subprocess
import time

import attr

from pyborg.mod.base import PyborgModBase

logger = logging.getLogger(__name__)


@attr.s
class KeybaseCommander(object):
    def run_command(self, cmd):
        command_to_exec = ["keybase", "chat", "api", "-m", json.dumps(cmd)]
        ret = subprocess.run(command_to_exec, capture_output=True)
        ret.check_returncode()
        try:
            parsed = json.loads(ret.stdout)
        except:
            logger.exception()
            logger.info(ret.stdout)
        return parsed

    def list(self):
        return self.run_command({"method": "list"})

    def send(self, channel, message):
        return self.run_command({"method": "send", "params": {"options": {"channel": channel, "message": message}}})

    def read(self, channel):
        return self.run_command({"method": "read", "params": {"options": {"channel": {"name": channel}}}})

    def join(self, chat_name):
        pass


@attr.s
class PyborgKeybase(PyborgModBase):

    def process_messages(self):
        logger.info("process_messages %s", self.cmdr.read("jackolas,jackolas"))

    def start(self):
        self.cmdr = KeybaseCommander()
        logger.info(self.cmdr.list())
        # scheduled run loop
        while True:
            self.process_messages()
            time.sleep(self.settings['cooldown'])
