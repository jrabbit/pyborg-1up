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
import getpass
import logging

import requests
from prompt_toolkit import prompt
from prompt_toolkit.history import InMemoryHistory

logger = logging.getLogger(__name__)
history = InMemoryHistory()


# class PyborgCommandSuggest(AutoSuggest):
#    "NB: for pt v2"
#     def __init__(self):
#         super(PyborgCommandSuggest, self).__init__()

#     def get_suggestion(self, buffer, document):
#         #use document.text
#         if document.text.startswith("!"):
#             return Suggestion("!quit")
#         return None


class ModLineIn():
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
        # self.completer = WordCompleter(["!quit"])
        self.start()

    def start(self):
        print("PyBorg offline chat!")
        print("Type !quit to leave")
        default = getpass.getuser()
        print("[{}]".format(default))
        self.name = prompt("What is your name? ")
        if self.name == "\n":
            self.name = default
        while 1:
            # body = prompt('> ', history=history, completer=self.completer)
            body = prompt('> ', history=history)
            if body == "":
                continue
            if body == "!quit":
                return

            # Pass message to borg
            if self.multiplexed:
                d = {"body": body, "reply_rate": 100, "learning": 1, "owner": 1}
                resp = requests.post("http://localhost:2001/process", data=d)

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
