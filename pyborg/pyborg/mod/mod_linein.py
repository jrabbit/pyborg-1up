#!/usr/bin/env python
#
# PyBorg Offline line input module
#
# Copyright (c) 2000, 2006, 2016-2017 Tom Morton, Sebastien Dailly, Jack Laxson
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
import logging
import string
import sys

import requests
import six
from pyborg import pyborg

logger = logging.getLogger(__name__)


class ModLineIn(object):

    """
    Module to interface console input and output with the PyBorg learn
    and reply modules. Allows offline chat with PyBorg.
    """
    # Command list for this module
    commandlist = "LineIn Module Commands:\n!quit"
    commanddict = {
        "quit": "Usage: !quit\nQuits pyborg and saves the dictionary"}

    def __init__(self, my_pyborg, multiplexed):
        self.multiplexed = multiplexed
        if not multiplexed:
            self.pyborg = my_pyborg()
        self.start()

    def start(self):
        print("PyBorg offline chat!")
        print("Type !quit to leave")
        print("What is your name")
        if six.PY2:
            self.name = raw_input("? ")
        else:
            self.name = input("? ")
        while 1:
            try:
                if six.PY2:
                    body = raw_input("> ")
                else:
                    body = input("> ")
            except (KeyboardInterrupt, EOFError) as e:
                print()
                return
            if body == "":
                continue
            if body == "!quit":
                return
            # Pass message to borg
            if self.multiplexed:
                d = {"body": body, "reply_rate": 100, "learning": 1, "owner": 1}
                resp = requests.post("http://localhost:2001/process", data=d)
                #resp.raise_for_status()
                if resp.status_code == requests.codes.ok:
                    self.output(resp.text, None)
                else:
                    logger.error(resp)
            else:
                self.pyborg.process_msg(self, body, 100, 1, (self.name), owner=1)

    def save(self):
        self.pyborg.save_all()

    def output(self, message, args):
        """
        Output a line of text.
        """
        message = message.replace("#nick", self.name)
        print(message)
