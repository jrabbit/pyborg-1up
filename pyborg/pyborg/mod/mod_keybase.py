import logging
import json
import subprocess
import time

import attr
from box import Box

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
    target_channel = attr.ib(default="jackolas,jackolas")

    def send(self, body):
        result = Box(self.cmdr.send(self.target_channel, body)).result
        logger.info(result)

    def process_messages(self):
        result = Box(self.cmdr.read("jackolas,jackolas")["result"])
        for msg in result.messages:
            body = msg.msg.content.text.body
            logger.info("process_messages: %s", body)
            self.learn(body)
            reply_message = self.reply(body)
            if reply_message:
                self.send(reply_message)

    def start(self):
        self.cmdr = KeybaseCommander()
        # logger.info(self.cmdr.list())
        # scheduled run loop
        while True:
            self.process_messages()
            time.sleep(self.settings['cooldown'])
