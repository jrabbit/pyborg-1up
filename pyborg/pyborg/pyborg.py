#
# PyBorg: The python AI bot.
#
# Copyright (c) 2000, 2006, 2013-2021 Tom Morton, Sebastien Dailly, Jack Laxson
#
#
# This bot was inspired by the PerlBorg, by Eric Bock.
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
# Tom Morton <tom@moretom.net>
# Seb Dailly <seb.dailly@gmail.com>
# Jack Laxson <jackjrabbit+pyborg@gmail.com>

import collections
import datetime
import json
import logging
import marshal
import os
import random
import re
import sys
import time
import uuid
import zipfile
from pathlib import Path
from random import randint
from typing import Any, Dict, Optional, Tuple, List, Callable, Union
from zlib import crc32

import attr
import click
import toml

from pyborg.util.censored_defaults import CENSORED_REASONABLE_DEFAULTS
from pyborg.util.util_cli import mk_folder

from . import __version__

logger = logging.getLogger(__name__)

try:
    import nltk
    logger.debug("Got nltk!")
except ImportError:
    nltk = None
    logger.debug("No nltk, won't be using advanced part of speech tagging.")

try:
    import systemd.daemon
except ImportError:
    systemd = None
    logger.debug("no systemd support detected")


def filter_message(message: str, bot) -> str:
    """
    Filter a message body so it is suitable for learning from and
    replying to. This involves removing confusing characters,
    padding ? and ! with ". " so they also terminate lines
    and converting to lower case.
    """
    # to lowercase
    message = message.lower()

    # remove garbage
    message = message.replace("\"", "")  # remove "s
    message = message.replace("\n", " ")  # remove newlines
    message = message.replace("\r", " ")  # remove carriage returns

    # remove matching brackets (unmatched ones are likely smileys :-) *cough*
    # should except out when not found.
    index = 0
    try:
        while 1:
            index = message.index("(", index)
            # Remove matching ) bracket
            i = message.index(")", index + 1)
            message = message[0:i] + message[i + 1:]
            # And remove the (
            message = message[0:index] + message[index + 1:]
    except ValueError as e:
        logger.debug("filter_message error: %s", e)

    message = message.replace(";", ",")
    message = message.replace("?", " ? ")
    message = message.replace("!", " ! ")
    message = message.replace(".", " . ")
    message = message.replace(",", " , ")
    message = message.replace("'", " ' ")
    message = message.replace(":", " : ")

    # Find ! and ? and append full stops.
    #   message = message.replace(". ", ".. ")
    #   message = message.replace("? ", "?. ")
    #   message = message.replace("! ", "!. ")

    #   And correct the '...'
    #   message = message.replace("..  ..  .. ", ".... ")

    words = message.split()
    for x in range(0, len(words)):
        # is there aliases ?
        for z in bot.settings.aliases.keys():
            for alias in bot.settings.aliases[z]:
                pattern = "^%s$" % alias
                if re.search(pattern, words[x]):
                    words[x] = z

    message = " ".join(words)
    return message


@attr.s
class FakeCfg2:
    """fake it until you make it"""

    aliases: dict = attr.ib(default={})
    num_aliases: int = attr.ib(default=0)
    censored: List[str] = attr.ib(default=CENSORED_REASONABLE_DEFAULTS, repr=False)
    ignore_list: list = attr.ib(default=[])
    max_words: int = attr.ib(default=6000)
    num_words: int = attr.ib(default=0)
    num_contexts: int = attr.ib(default=0)
    no_save: bool = attr.ib(default=False)
    learning: bool = attr.ib(default=True)

    def save(self) -> None:
        logger.debug("Settings save called. Current state: %s", self)


class FakeAns:
    """this is a cool thing"""
    def __init__(self) -> None:
        self.sentences = {}


@attr.s
class InternalCommand:
    name: str = attr.ib()
    function: Callable[..., str] = attr.ib()
    help: Union[str, bool] = attr.ib()
    input: bool = attr.ib(default=False)

    def get_help(self):
        if help is True:
            # introsepct the function here
            return self.function.__doc__
        return self.help


def checkdict(pyb: "PyborgExperimental") -> str:
    "Check for broken links in the dictionary"
    t = time.time()
    num_broken = 0
    num_bad = 0
    for w in pyb.words.keys():
        wlist = pyb.words[w]
        for i in range(len(wlist) - 1, -1, -1):
            line_idx = wlist[i]['hashval']
            word_num = wlist[i]['index']
            # Nasty critical error we should fix
            if line_idx not in pyb.lines:
                logging.debug("Removing broken link '%s' -> %d" % (w, line_idx))
                num_broken = num_broken + 1
                del wlist[i]
            else:
                # Check pointed to word is correct
                split_line = pyb.lines[line_idx][0].split()
                if split_line[word_num] != w:
                    logging.error("Line '%s' word %d is not '%s' as expected." % (pyb.lines[line_idx][0], word_num, w))
                    num_bad = num_bad + 1
                    del wlist[i]
        if len(wlist) == 0:
            del pyb.words[w]
            pyb.settings.num_words = pyb.settings.num_words - 1
            logging.info("\"%s\" vaped totally" % w)

    output = "Checked dictionary in %0.2fs. Fixed links: %d broken, %d bad." % (time.time() - t, num_broken, num_bad)
    logging.info(output)
    return output


def known_command(pyb: "PyborgExperimental", word: str) -> str:
    if word in pyb.words:
        c = len(pyb.words[word])
        msg = "%s is known (%d contexts)" % (word, c)
    else:
        msg = "%s is unknown." % word
    return msg


def known2(pyb, words: List[str]) -> str:
    msg = "Number of contexts: "
    for x in words:
        if x in pyb.words:
            c = len(pyb.words[x])
            msg += x + "/" + str(c) + " "
        else:
            msg += x + "/0 "
    return msg


def _internal_commands_generate() -> Dict:
    return {"checkdict": InternalCommand(name="checkdict", function=checkdict, help="check the brain for broken links (legacy)"),
            "known": InternalCommand(name="known", function=known_command, input=True, help=True)}

def _create_new_database() -> str:
    mk_folder()
    folder = click.get_app_dir("Pyborg")
    name = datetime.datetime.now().strftime("%m-%d-%y-auto-{}.pyborg.json").format(str(uuid.uuid4())[:4])
    brain_path = os.path.join(folder, "brains", name)
    logger.info("Error reading saves. New database created.")
    return brain_path


def PyborgBridge(brain: Any) -> "PyborgExperimental":
    "cheat and make an api mapping to the old one"
    mk_folder()
    logger.info("Reading dictionary...")
    try:
        their_pyb = PyborgExperimental.from_brain(brain)
    except (EOFError, IOError) as e:
        # Create new database
        logger.debug(e)
        folder = click.get_app_dir("Pyborg")
        name = datetime.datetime.now().strftime("%m-%d-%y-auto-{}.pyborg.json").format(str(uuid.uuid4())[:4])
        brain_path = Path(folder, "brains", name)
        logger.info("Error reading saves. New database created.")
        their_pyb = PyborgExperimental(brain=brain_path, words={}, lines={})
    return their_pyb



@attr.s
class PyborgExperimental:
    brain: Path = attr.ib()
    words: Dict[str, Dict[str, int]] = attr.ib()
    lines: Dict[int, Tuple[str, int]] = attr.ib()
    settings_file: Path = attr.ib(default=Path(click.get_app_dir("Pyborg"), "pyborg.toml"))
    settings: FakeCfg2 = attr.ib(default=FakeCfg2())
    internal_commands: Dict[str, InternalCommand] = attr.ib(default=_internal_commands_generate())
    ver_string: str = attr.ib(default=f"I am a version {__version__} Pyborg")
    saves_version: str = attr.ib(default="1.4.0")
    ready: bool = attr.ib(default=False)
    has_nltk: bool = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        if nltk is None:
            self.has_nltk = False
        else:
            self.has_nltk = True

    def __repr__(self) -> str:
        return f"{self.ver_string} with {len(self.words)} words and {len(self.lines)} lines. With a settings of: {self.settings}"

    def __str__(self) -> str:
        return self.ver_string

    def on_ready(self):
        """does nothing! implement or override. used internally for systemd notify."""
        pass

    @classmethod
    def from_brain(cls, brain: Path) -> "PyborgExperimental":
        words, lines = pyborg.load_brain_json(brain)
        # READY can be sent here
        instance = cls(brain=brain, lines=lines, words=words)
        instance.on_ready()
        instance.ready = True
        return instance

    def make_reply(self, body: str) -> str:
        pass

    def learn(self, body: str) -> None:
        pass

    def save(self) -> None:
        """
        Save brain as 1.4.0 JSON-Unsigned format
        """
        logger.info("Writing dictionary...")

        folder = click.get_app_dir("Pyborg")
        logger.info("Saving pyborg brain to %s", self.brain)
        cnt: collections.Counter = collections.Counter()
        for key, value in self.words.items():
            cnt[type(key)] += 1
            # cnt[type(value)] += 1
            for i in value:
                cnt[type(i)] += 1
        logger.debug("Types: %s", cnt)
        logger.debug("Words: %s", self.words)
        logger.debug("Lines: %s", self.lines)

        brain = {'version': self.saves_version, 'words': self.words, 'lines': self.lines}
        tmp_file = os.path.join(folder, "tmp", "current.pyborg.json")
        with open(tmp_file, 'w') as f:
            # this can fail half way...
            json.dump(brain, f)
        # if we didn't crash
        os.rename(tmp_file, self.brain)
        logger.debug("Successful writing of brain & renaming. Quitting.")


class PyborgSystemdNotify(PyborgExperimental):
    def on_ready(self):
        systemd.daemon.notify('READY=1')


class PyborgEmptyJSON(Exception):
    pass


class PyborgNoBrainException(Exception):
    pass


class pyborg:

    ver_string = "I am a version 2.0.0 Pyborg"
    saves_version = "1.4.0"

    # Main command list
    commandlist = "Pyborg commands:\n!checkdict, !contexts, !help, !known, !learning, !rebuilddict, \
!replace, !unlearn, !purge, !version, !words, !limit, !alias, !save, !censor, !uncensor, !owner"
    commanddict = {
        "help": "Owner command. Usage: !help [command]\nPrints information about using a command, or a list of commands if no command is given",
        "version": "Usage: !version\nDisplay what version of Pyborg we are running",
        "words": "Usage: !words\nDisplay how many words are known",
        "known": "Usage: !known word1 [word2 [...]]\nDisplays if one or more words are known, and how many contexts are known",
        "contexts": "Owner command. Usage: !contexts <phrase>\nPrint contexts containing <phrase>",
        "unlearn": "Owner command. Usage: !unlearn <expression>\nRemove all occurances of a word or expression from the dictionary. For example '!unlearn of of' would remove all contexts containing double 'of's",
        "purge": "Owner command. Usage: !purge [number]\nRemove all occurances of the words that appears in less than <number> contexts",
        "replace": "Owner command. Usage: !replace <old> <new>\nReplace all occurances of word <old> in the dictionary with <new>",
        "learning": "Owner command. Usage: !learning [on|off]\nToggle bot learning. Without arguments shows the current setting",
        "checkdict": "Owner command. Usage: !checkdict\nChecks the dictionary for broken links. Shouldn't happen, but worth trying if you get KeyError crashes",
        "rebuilddict": "Owner command. Usage: !rebuilddict\nRebuilds dictionary links from the lines of known text. Takes a while. You probably don't need to do it unless your dictionary is very screwed",
        "censor": "Owner command. Usage: !censor [word1 [...]]\nPrevent the bot using one or more words. Without arguments lists the currently censored words",
        "uncensor": "Owner command. Usage: !uncensor word1 [word2 [...]]\nRemove censorship on one or more words",
        "limit": "Owner command. Usage: !limit [number]\nSet the number of words that pyBorg can learn",
        "alias": "Owner command. Usage: !alias : Show the differents aliases\n!alias <alias> : show the words attached to this alias\n!alias <alias> <word> : link the word to the alias",
        "owner": "Usage : !owner password\nAdd the user in the owner list"
    }

    @staticmethod
    def load_brain_2(brain_path: Union[str, Path]) -> Tuple[Dict, Dict]:
        """1.2.0 marshal.zip loader
        Returns tuple (words, lines)"""

        saves_version = b"1.2.0"

        try:
            zfile = zipfile.ZipFile(brain_path, 'r')
            for filename in zfile.namelist():
                data = zfile.read(filename)
                f = open(filename, 'w+b')
                f.write(data)
                f.close()
        except (EOFError, IOError) as e:
            logger.debug(e)
            print("no zip found")
            logger.info("No archive.zip (pyborg brain) found.")

        with open("version", "rb") as vers, open("words.dat", "rb") as words, open("lines.dat", "rb") as lines:
            x = vers.read()
            logger.debug("Saves Version: %s", x)
            if x != saves_version:
                print("Error loading dictionary\nPlease convert it before launching pyborg")
                logger.error("Error loading dictionary\nPlease convert it before launching pyborg")
                logger.debug("Pyborg version: %s", saves_version)
                sys.exit(1)
            words = marshal.loads(words.read())
            lines = marshal.loads(lines.read())
        return words, lines

    @staticmethod
    def load_brain_json(brain_path: Union[Path, str]) -> Tuple[Dict[str, int], Dict[int, Tuple[str, int]]]:
        """Load the new format"""
        saves_version = u"1.4.0"
        # folder = click.get_app_dir("Pyborg")
        logger.debug("Trying to open brain %s", brain_path)
        with open(brain_path) as f:
            raw_json = f.read()
        logger.debug(raw_json)
        try:
            brain = json.loads(raw_json)
        except json.decoder.JSONDecodeError as e:
            logger.exception(e)
            logger.info("Tried to open brain %s", brain_path)
            # if the file is just empty for instance a Tempfile from `tempfile` just record it and raise a less scary error.
            # wrapping Paths is fine apparently... probably nasty but whatever

            if Path(brain_path).stat().st_size < 2:
                raise PyborgEmptyJSON from e
            else:
                raise e
        if brain['version'] == saves_version:
            logger.debug(brain['lines'])
            lines = {int(x): y for x, y in brain['lines'].items()}
            return brain['words'], lines
        else:
            print("Error loading dictionary\nPlease convert it before launching pyborg")
            logger.error("Error loading dictionary\nPlease convert it before launching pyborg")
            logger.debug("Pyborg version: %s", saves_version)
            raise PyborgNoBrainException()

    def save_brain(self) -> None:
        """
        Save brain as 1.4.0 JSON-Unsigned format
        """
        logger.info("Writing dictionary...")

        saves_version = u"1.4.0"
        folder = click.get_app_dir("Pyborg")
        logger.info("Saving pyborg brain to %s", self.brain_path)
        cnt = collections.Counter()
        for key, value in self.words.items():
            cnt[type(key)] += 1
            # cnt[type(value)] += 1
            for i in value:
                cnt[type(i)] += 1
        logger.debug("Types: %s", cnt)
        logger.debug("Words: %s", self.words)
        logger.debug("Lines: %s", self.lines)

        brain = {'version': saves_version, 'words': self.words, 'lines': self.lines}
        tmp_file = os.path.join(folder, "tmp", "current.pyborg.json")
        with open(tmp_file, 'w') as f:
            # this can fail half way...
            json.dump(brain, f)
        # if we didn't crash
        os.rename(tmp_file, self.brain_path)
        logger.debug("Successful writing of brain & renaming.")

    def save_all(self) -> None:
        "Legacy wraper for save_brain()"
        self.save_brain()

    def load_settings(self) -> FakeCfg2:
        toml_path = os.path.join(click.get_app_dir("Pyborg"), "pyborg.toml")

        if os.path.exists(click.get_app_dir("Pyborg")) and not os.path.exists(toml_path):
            settings = {'pyborg-core': {"max_words": False}}
            toml.dump(settings, open(toml_path, "w"))

        d = toml.load(toml_path)['pyborg-core']
        if d['max_words']:
            cfg = FakeCfg2(max_words=d['max_words'])
        else:
            cfg = FakeCfg2(max_words=50000)
        return cfg

    def __repr__(self) -> str:
        return "{} with {} words and {} lines. With a settings of: {}".format(self.ver_string, len(self.words), len(self.lines), self.settings)

    def __init__(self, brain: Union[str, Path, None] = None) -> None:
        """
        Open the dictionary. Resize as required.
        """

        self.settings = self.load_settings()
        self.answers = FakeAns()
        self.unfilterd = {}
        mk_folder()

        # Read the dictionary
        logger.info("Reading dictionary...")
        if brain is None:
            self.brain_path = 'archive.zip'
        else:
            self.brain_path = brain
        try:
            self.words, self.lines = self.load_brain_json(self.brain_path)
        except (EOFError, IOError, json.decoder.JSONDecodeError, PyborgEmptyJSON) as e:
            # Create new database
            self.words = {}
            self.lines = {}
            logger.error(e)
            folder = click.get_app_dir("Pyborg")
            name = datetime.datetime.now().strftime("%m-%d-%y-auto-{}.pyborg.json").format(str(uuid.uuid4())[:4])
            self.brain_path = os.path.join(folder, "brains", name)
            logger.info("Error reading saves. New database created.")

        # Is a resizing required?
        if len(self.words) != self.settings.num_words:
            logger.info("Updating dictionary information...")
            self.settings.num_words = len(self.words)
            num_contexts = 0
            # Get number of contexts
            for x in self.lines.keys():
                num_contexts += len(self.lines[x][0].split())
            self.settings.num_contexts = num_contexts
            # Save new values
            self.settings.save()

        # Is an aliases update required ?
        compteur = 0
        for x in self.settings.aliases.keys():
            compteur += len(self.settings.aliases[x])
        if compteur != self.settings.num_aliases:
            logger.info("check dictionary for new aliases")
            self.settings.num_aliases = compteur

            for x in self.words.keys():
                # is there aliases ?
                if x[0] != '~':
                    for z in self.settings.aliases.keys():
                        for alias in self.settings.aliases[z]:
                            pattern = "^%s$" % alias
                            if re.search(pattern, x):
                                logger.info("replace %s with %s", x, z)
                                self.replace(x, z)

            for x in self.words.keys():
                if not (x in self.settings.aliases.keys()) and x[0] == '~':
                    logger.info("unlearn %s" % x)
                    self.settings.num_aliases -= 1
                    self.unlearn(x)
                    logger.info("unlearned aliases %s" % x)

        # unlearn words in the unlearn.txt file.
        try:
            with open("unlearn.txt", 'r') as f:
                for line in f.readlines():
                    self.unlearn(line)
        except (EOFError, IOError) as e:
            logger.debug("No words to unlearn")
        self.settings.save()

    def save_all_2(self):
        "legacy api"
        if self.settings.no_save != "True":
            print("Writing dictionary...")

            try:
                zfile = zipfile.ZipFile(self.brain_path, 'r')
                for filename in zfile.namelist():
                    data = zfile.read(filename)
                    f = open(filename, 'w+b')
                    f.write(data)
                    f.close()
            except (OSError, IOError):
                print("no zip found. Is the programm launch for first time ?")

            with open("words.dat", "wb") as f:
                f.write(marshal.dumps(self.words))

            with open("lines.dat", "wb") as f:
                f.write(marshal.dumps(self.lines))

            # save the version
            with open('version', 'w') as f:
                f.write(self.saves_version)

            # zip the files
            with zipfile.ZipFile(self.brain_path, "w") as f:
                f.write('words.dat')
                f.write('lines.dat')
                f.write('version')

            try:
                os.remove('words.dat')
                os.remove('lines.dat')
                os.remove('version')
            except (OSError, IOError):
                print("could not remove the files")

            f = open("words.txt", "w")
            # write each words known
            wordlist = []
            # Sort the list befor to export
            for key in self.words:
                wordlist.append([key, len(self.words[key])])
            wordlist.sort(key=lambda x: x[1])
            list(map((lambda x: f.write(str(x[0]) + "\n\r")), wordlist))
            f.close()

            f = open("sentences.txt", "w")
            # write each words known
            wordlist = []
            # Sort the list befor to export
            for key in self.unfilterd:
                wordlist.append([key, self.unfilterd[key]])
            # wordlist.sort(lambda x, y: cmp(y[1], x[1]))
            wordlist.sort(key=lambda x: x[1])
            list(map((lambda x: f.write(str(x[0]) + "\n")), wordlist))
            f.close()

            # Save settings
            self.settings.save()

    def process_msg(self, io_module, body, replyrate, learn: int, args, owner=0) -> None:
        """
        Process message 'body' and pass back to IO module with args.
        If owner==1 allow owner commands.
        """
        logger.debug("process_msg: %s", locals())
        # add trailing space so sentences are broken up correctly
        body = body + " "

        # Parse commands
        if body[0] == "!":
            logger.debug("sending do_commands...")
            self.do_commands(io_module, body, args, owner)
            return

        # Filter out garbage and do some formatting
        body = filter_message(body, self)

        # Learn from input
        if learn == 1:
            self.learn(body)

        # Make a reply if desired
        if randint(0, 99) < int(replyrate):

            message = ""

            # Look if we can find a prepared answer
            for sentence in self.answers.sentences.keys():
                pattern = "^%s$" % sentence
                if re.search(pattern, body):
                    message = self.answers.sentences[sentence][
                        randint(0, len(self.answers.sentences[sentence]) - 1)]
                    break
                else:
                    if body in self.unfilterd:
                        self.unfilterd[body] = self.unfilterd[body] + 1
                    else:
                        self.unfilterd[body] = 0

            if message == "":
                message = self.reply(body)

            # single word reply: always output
            if len(message.split()) == 1:
                io_module.output(message, args)
                return
            # empty. do not output
            if message == "":
                return
            # else output
            if owner == 0:
                time.sleep(.2 * len(message))
            io_module.output(message, args)

    def do_commands(self, io_module, body: str, args, owner: int) -> None:
        """
        Respond to user commands.
        """
        msg = ""
        command_list = body.split()
        logger.debug("do_commands.command_list: %s", command_list)
        command_list[0] = command_list[0].lower()
        # Guest commands.
        # Version string
        if command_list[0] == "!version":
            msg = self.ver_string

        # How many words do we know?
        elif command_list[0] == "!words":
            num_w = self.settings.num_words
            num_c = self.settings.num_contexts
            num_l = len(self.lines)
            if num_w != 0:
                num_cpw = num_c / float(num_w)  # contexts per word
            else:
                num_cpw = 0.0
            msg = "I know %d words (%d contexts, %.2f per word), %d lines." % (num_w, num_c, num_cpw, num_l)

        # Owner commands
        if owner == 1:
            # Save dictionary
            if command_list[0] == "!save":
                self.save_all()
                msg = "Dictionary saved"

            # Command list
            elif command_list[0] == "!help":
                if len(command_list) > 1:
                    # Help for a specific command
                    cmd = command_list[1].lower()
                    dic = None
                    if cmd in self.commanddict.keys():
                        dic = self.commanddict
                    elif cmd in io_module.commanddict.keys():
                        dic = io_module.commanddict
                    if dic:
                        for i in dic[cmd].split("\n"):
                            io_module.output(i, args)
                    else:
                        msg = "No help on command '%s'" % cmd
                else:
                    for i in self.commandlist.split("\n"):
                        io_module.output(i, args)
                    for i in io_module.commandlist.split("\n"):
                        io_module.output(i, args)

            # Change the max_words setting
            elif command_list[0] == "!limit":
                msg = "The max limit is "
                if len(command_list) == 1:
                    msg += str(self.settings.max_words)
                else:
                    limit = int(command_list[1].lower())
                    self.settings.max_words = limit
                    msg += "now " + command_list[1]

            # Rebuild the dictionary by discarding the word links and
            # re-parsing each line
            elif command_list[0] == "!rebuilddict":
                if self.settings.learning == 1:
                    t = time.time()

                    old_lines = self.lines
                    old_num_words = self.settings.num_words
                    old_num_contexts = self.settings.num_contexts

                    self.words = {}
                    self.lines = {}
                    self.settings.num_words = 0
                    self.settings.num_contexts = 0

                    for k in old_lines.keys():
                        self.learn(old_lines[k][0], old_lines[k][1])

                    msg = "Rebuilt dictionary in %0.2fs. Words %d (%+d), contexts %d (%+d)" % (time.time() - t, old_num_words, self.settings.num_words - old_num_words, old_num_contexts, self.settings.num_contexts - old_num_contexts)

            # Remove rares words
            elif command_list[0] == "!purge":
                t = time.time()
                if len(command_list) == 2:
                    # limite d occurences a effacer
                    c_max = int(command_list[1])
                else:
                    c_max = 0
                number_removed = self.purge(c_max, io_module=io_module)
                msg = "Purge dictionary in %0.2fs. %d words removed" % (time.time() - t, number_removed)

            # Change a typo in the dictionary
            elif command_list[0] == "!replace":
                if len(command_list) < 3:
                    return
                old = command_list[1].lower()
                new = command_list[2].lower()
                msg = self.replace(old, new)

            # Print contexts [flooding...:-]
            elif command_list[0] == "!contexts":
                # This is a large lump of data and should
                # probably be printed, not module.output XXX

                # build context we are looking for
                context = " ".join(command_list[1:])
                context = context.lower()
                if context == "":
                    return
                io_module.output("Contexts containing \"" + context + "\":", args)
                # Build context list
                # Pad it
                context = " " + context + " "
                c = []
                # Search through contexts
                for x in self.lines.keys():
                    # get context
                    ctxt = self.lines[x][0]
                    # add leading whitespace for easy sloppy search code
                    ctxt = " " + ctxt + " "
                    if ctxt.find(context) != -1:
                        # Avoid duplicates (2 of a word
                        # in a single context)
                        if len(c) == 0:
                            c.append(self.lines[x][0])
                        elif c[len(c) - 1] != self.lines[x][0]:
                            c.append(self.lines[x][0])
                x = 0
                while x < 5:
                    if x < len(c):
                        io_module.output(c[x], args)
                    x += 1
                if len(c) == 5:
                    return
                if len(c) > 10:
                    io_module.output("...({} skipped)...".format(len(c) - 10), args)
                x = len(c) - 5
                if x < 5:
                    x = 5
                while x < len(c):
                    io_module.output(c[x], args)
                    x += 1

            # Remove a word from the vocabulary [use with care]
            elif command_list[0] == "!unlearn":
                # build context we are looking for
                context = " ".join(command_list[1:])
                context = context.lower()
                if context == "":
                    return
                print("Looking for: " + context)
                # Unlearn contexts containing 'context'
                t = time.time()
                self.unlearn(context)
                # we don't actually check if anything was
                # done..
                msg = "Unlearn done in %0.2fs" % (time.time() - t)

            # Query/toggle bot learning
            elif command_list[0] == "!learning":
                msg = "Learning mode "
                if len(command_list) == 1:
                    if self.settings.learning == 0:
                        msg += "off"
                    else:
                        msg += "on"
                else:
                    toggle = command_list[1].lower()
                    if toggle == "on":
                        msg += "on"
                        self.settings.learning = 1
                    else:
                        msg += "off"
                        self.settings.learning = 0

            # add a word to the 'censored' list
            elif command_list[0] == "!censor":
                # no arguments. list censored words
                if len(command_list) == 1:
                    if len(self.settings.censored) == 0:
                        msg = "No words censored"
                    else:
                        msg = "I will not use the word(s) %s" % ", ".join(self.settings.censored)
                # add every word listed to censored list
                else:
                    for x in range(1, len(command_list)):
                        if command_list[x] in self.settings.censored:
                            msg += "%s is already censored" % command_list[x]
                        else:
                            self.settings.censored.append(command_list[x].lower())
                            self.unlearn(command_list[x])
                            msg += "done"
                        msg += "\n"

            # remove a word from the censored list
            elif command_list[0] == "!uncensor":
                # Remove everyone listed from the ignore list
                # eg !unignore tom dick harry
                for x in range(1, len(command_list)):
                    try:
                        self.settings.censored.remove(command_list[x].lower())
                        msg = "done"
                    except ValueError as e:
                        logger.exception(e)

            elif command_list[0] == "!alias":
                # no arguments. list aliases words
                if len(command_list) == 1:
                    if len(self.settings.aliases) == 0:
                        msg = "No aliases"
                    else:
                        msg = "I will alias the word(s) %s" % ", ".join(self.settings.aliases.keys())
                # add every word listed to alias list
                elif len(command_list) == 2:
                    if command_list[1][0] != '~':
                        command_list[1] = '~' + command_list[1]
                    if command_list[1] in self.settings.aliases.keys():
                        msg = "Thoses words : %s  are aliases to %s" % (" ".join(self.settings.aliases[command_list[1]]), command_list[1])
                    else:
                        msg = "The alias %s is not known" % command_list[1][1:]
                elif len(command_list) > 2:
                    # create the aliases
                    msg = "The words : "
                    if command_list[1][0] != '~':
                        command_list[1] = '~' + command_list[1]
                    if not(command_list[1] in self.settings.aliases.keys()):
                        self.settings.aliases[command_list[1]] = [command_list[1][1:]]
                        self.replace(command_list[1][1:], command_list[1])
                        msg += command_list[1][1:] + " "
                    for x in range(2, len(command_list)):
                        msg += "%s " % command_list[x]
                        self.settings.aliases[command_list[1]].append(command_list[x])
                        # replace each words by his alias
                        self.replace(command_list[x], command_list[1])
                    msg += "have been aliases to %s" % command_list[1]

            # Quit
            elif command_list[0] == "!quit":
                # Close the dictionary
                self.save_all()
                sys.exit()

            # Save changes
            self.settings.save()
        logger.info(msg)
        if msg != "":
            io_module.output(msg, args)

    def replace(self, old: str, new: str) -> str:
        """
        Replace all occuraces of 'old' in the dictionary with
        'new'. Nice for fixing learnt typos.
        """
        try:
            pointers = self.words[old]
        except KeyError:
            return old + " not known."
        changed = 0

        for x in pointers:
            # pointers consist of (line, word) to self.lines
            l = self.words[x['hashval']]  # noqa: E741
            w = self.words[x['index']]
            line = self.lines[l][0].split()
            number = self.lines[l][1]
            if line[w] != old:
                # fucked dictionary
                print("Broken link: %s %s" % (x, self.lines[l][0]))
                continue

            line[w] = new
            self.lines[l][0] = " ".join(line)
            self.lines[l][1] += number
            changed += 1

        if new in self.words:
            self.settings.num_words -= 1
            self.words[new].extend(self.words[old])
        else:
            self.words[new] = self.words[old]
        del self.words[old]
        return "%d instances of %s replaced with %s" % (changed, old, new)

    def purge(self, max_contexts: int, io_module=None) -> int:
        "Remove rare words from the dictionary. Returns number of words removed."
        liste = []
        compteur = 0

        for w in self.words.keys():
            digit = 0
            char = 0
            for c in w:
                if c.isalpha():
                    char += 1
                if c.isdigit():
                    digit += 1

        # Compte les mots inferieurs a cette limite
            c = len(self.words[w])
            if c < 2 or (digit and char):
                liste.append(w)
                compteur += 1
                if compteur == max_contexts:
                    break

        if max_contexts < 1:
            # io_module.output(str(compteur)+" words to remove", args)
            if io_module:
                # I'm not gonna pass pyborg.process.args. This breaks the api technically.
                io_module.output("%s words to remove" % compteur, [])

        # supprime les mots
        for w in liste[0:]:
            self.unlearn(w)
        return len(liste[0:])

    def unlearn(self, context: str) -> None:
        """
        Unlearn all contexts containing 'context'. If 'context'
        is a single word then all contexts containing that word
        will be removed, just like the old !unlearn <word>
        """
        # Pad thing to look for
        # We pad so we don't match 'shit' when searching for 'hit', etc.
        context = " " + context + " "
        # Search through contexts
        # count deleted items
        dellist = []
        # words that will have broken context due to this
        wordlist = []
        for x in self.lines.copy().keys():
            # get context. pad
            c = " " + self.lines[x][0] + " "
            if c.find(context) != -1:
                # Split line up
                wlist = self.lines[x][0].split()
                # add touched words to list
                for w in wlist:
                    if w not in wordlist:
                        wordlist.append(w)
                dellist.append(x)
                del self.lines[x]
        words = self.words
        # update links
        for x in wordlist:
            word_contexts = words[x]
            # Check all the word's links (backwards so we can delete)
            for y in range(len(word_contexts) - 1, -1, -1):
                # Check for any of the deleted contexts
                hashval = word_contexts[y]['hashval']
                if hashval in dellist:
                    del word_contexts[y]
                    self.settings.num_contexts = self.settings.num_contexts - 1
            if len(words[x]) == 0:
                del words[x]
                self.settings.num_words = self.settings.num_words - 1
                logger.info(f" \"{x}\" vaped totally")

    def _is_censored(self, word: str) -> bool:
        """DRY."""
        for censored in self.settings.censored:
            if re.search(censored, word):
                logger.debug(f"word is censored: {word}")
                return True
        return False

    def reply(self, body) -> Optional[str]:
        """
        Reply to a line of text.
        """
        # split sentences into list of words
        _words = body.split(" ")
        words = []
        for i in _words:
            words += i.split()

        if len(words) == 0:
            logger.debug("Did not find any words to reply to.")
            return None

        # remove words on the ignore list
        words = [x for x in words if x not in self.settings.ignore_list and not x.isdigit()]
        logger.debug("reply: cleaned words: %s", words)
        # Find rarest word (excluding those unknown)
        index = []
        known = -1
        # The word has to have been seen in already 3 contexts differents for being choosen
        known_min = 3
        for w in words:
            logger.debug("known_loop: locals: %s", locals())
            if w in self.words:
                k = len(self.words[w])
                logger.debug("known_loop: k?? %s", k)
            else:
                continue
            if (known == -1 or k < known) and k > known_min:
                index = [w]
                known = k
                continue
            elif k == known:
                index.append(w)
                continue
        # Index now contains list of rarest known words in sentence
        # index = words

        # def find_known_words(words):
        #     d = dict()
        #     for w in words:
        #         if w in self.words:
        #             logger.debug(self.words[w])
        #             k = len(self.words[w])
        #             d[w] = k
        #     logger.debug("find_known_words: %s", d)
        #     idx = [x for x,y  in d.items() if y > 3]
        #     logger.debug("find_known_words: %s", idx)
        #     return idx

        # index = find_known_words(words)

        if len(index) == 0:
            logger.debug("No words with atleast 3 contexts were found.")
            logger.debug("reply:index: %s", index)
            return ""

        # Begin experimental NLP code
        def weight(pos: str) -> int:
            """Takes a POS tag and assigns a weight
            New: doubled the weights in 1.4"""
            lookup = {"NN": 8, "NNP": 10, "RB": 4, "NNS": 6, "NNPS": 10}
            try:
                ret = lookup[pos]
            except KeyError:
                ret = 2
            return ret

        def _mappable_nick_clean(pair: Tuple[str, str]) -> Tuple[str, int]:
            "mappable weight apply but with shortcut for #nick"
            word, pos = pair
            if word == "#nick":
                comp_weight = 1
            else:
                comp_weight = weight(pos)
            return (word, comp_weight)

        if nltk:
            # uses punkt
            tokenized = nltk.tokenize.casual.casual_tokenize(body)
            # uses averaged_perceptron_tagger
            tagged = nltk.pos_tag(tokenized)
            logger.info(tagged)
            weighted_choices = list(map(_mappable_nick_clean, tagged))
            population = [val for val, cnt in weighted_choices for i in range(cnt)]
            word = random.choice(population)
            # make sure the word is known
            counter = 0
            while word not in self.words and counter < 200:
                word = random.choice(population)
                counter += 1
            logger.debug("Ran choice %d times", counter)
        else:
            word = index[randint(0, len(index) - 1)]

        # Build sentence backwards from "chosen" word
        if self._is_censored(word):
            logger.debug("chosen word: %s***%s is censored. ignoring.", word[0], word[-1])
            return None
        sentence = [word]
        done = 0
        while done == 0:
            # create a dictionary wich will contain all the words we can found before the "chosen" word
            pre_words = {"": 0}
            # this is for prevent the case when we have an ignore_listed word
            word = str(sentence[0].split(" ")[0])
            for x in range(0, len(self.words[word]) - 1):
                logger.debug(locals())
                logger.debug('trying to unpack: %s', self.words[word][x])
                l = self.words[word][x]['hashval']  # noqa: E741
                w = self.words[word][x]['index']
                context = self.lines[l][0]
                num_context = self.lines[l][1]
                cwords = context.split()
                # if the word is not the first of the context, look the previous one
                if cwords[w] != word:
                    print(context)
                if w:
                    # look if we can found a pair with the choosen word, and the previous one
                    if len(sentence) > 1 and len(cwords) > w + 1:
                        if sentence[1] != cwords[w + 1]:
                            continue

                    # if the word is in ignore_list, look the previous word
                    look_for = cwords[w - 1]
                    if look_for in self.settings.ignore_list and w > 1:
                        look_for = cwords[w - 2] + " " + look_for

                    # saves how many times we can found each word
                    if look_for not in pre_words:
                        pre_words[look_for] = num_context
                    else:
                        pre_words[look_for] += num_context

                else:
                    pre_words[""] += num_context

            # Sort the words
            liste = list(pre_words.items())  # this is a view in py3
            liste.sort(key=lambda x: x[1])
            numbers = [liste[0][1]]
            for x in range(1, len(liste)):
                numbers.append(liste[x][1] + numbers[x - 1])

            # take one them from the list ( randomly )
            mot = randint(0, numbers[len(numbers) - 1])
            for x in range(0, len(numbers)):
                if mot <= numbers[x]:
                    mot = liste[x][0]
                    break

            # if the word is already choosen, pick the next one
            while mot in sentence:
                x += 1
                if x >= len(liste) - 1:
                    mot = ''
                logger.info("the choosening: %s", liste[x])
                mot = liste[x][0]

            # logger.debug("mot1: %s", len(mot))
            mot = mot.split()
            mot.reverse()
            if mot == []:
                done = 1
            else:
                list(map((lambda x: sentence.insert(0, x)), mot))

        pre_words = sentence
        sentence = sentence[-2:]

        # Now build sentence forwards from "chosen" word

        # We've got
        # cwords:    ... cwords[w-1] cwords[w]   cwords[w+1] cwords[w+2]
        # sentence:  ... sentence[-2]    sentence[-1]    look_for    look_for ?

        # we are looking, for a cwords[w] known, and maybe a cwords[w-1] known, what will be the cwords[w+1] to choose.
        # cwords[w+2] is need when cwords[w+1] is in ignored list
        done = 0
        while done == 0:
            # create a dictionary wich will contain all the words we can found before the "chosen" word
            post_words = {"": 0}
            word = str(sentence[-1].split(" ")[-1])
            for x in range(0, len(self.words[word])):
                l = self.words[word][x]['hashval']  # noqa: E741
                w = self.words[word][x]['index']
                context = self.lines[l][0]
                num_context = self.lines[l][1]
                cwords = context.split()
                # look if we can found a pair with the choosen word, and the next one
                if len(sentence) > 1:
                    if sentence[len(sentence) - 2] != cwords[w - 1]:
                        continue

                if w < len(cwords) - 1:
                    # if the word is in ignore_list, look the next word
                    look_for = cwords[w + 1]
                    if (look_for in self.settings.ignore_list or look_for in self.settings.censored) and w < len(cwords) - 2:
                        look_for = look_for + " " + cwords[w + 2]

                    if look_for not in post_words:
                        post_words[look_for] = num_context
                    else:
                        post_words[look_for] += num_context
                else:
                    post_words[""] += num_context
            # Sort the words
            liste = list(post_words.items())
            liste.sort(key=lambda x: x[1])
            numbers = [liste[0][1]]

            for x in range(1, len(liste)):
                numbers.append(liste[x][1] + numbers[x - 1])

            # take one them from the list ( randomly )
            mot = randint(0, numbers[len(numbers) - 1])
            for x in range(0, len(numbers)):
                if mot <= numbers[x]:
                    mot = liste[x][0]
                    break

            x = -1
            while mot in sentence:
                x += 1
                if x >= len(liste) - 1:
                    mot = ''
                    break
                mot = liste[x][0]

            # logger.debug("mot2: %s", len(mot))
            mot = mot.split()
            if mot == []:
                done = 1
            else:
                list(map(lambda x: sentence.append(x), mot))
        sentence = pre_words[:-2] + sentence
        # this seems bogus? how does this work???

        # Replace aliases
        for x in range(0, len(sentence)):
            if sentence[x][0] == "~":
                sentence[x] = sentence[x][1:]

        # Insert space between each words
        list(map((lambda x: sentence.insert(1 + x * 2, " ")), range(0, len(sentence) - 1)))

        # correct the ' & , spaces problem
        # code is not very good and can be improve but does his job...
        for x in range(0, len(sentence)):
            if sentence[x] == "'":
                sentence[x - 1] = ""
                sentence[x + 1] = ""
            if sentence[x] == ",":
                sentence[x - 1] = ""
        # logger.debug("final locals: %s", locals())
        # yolo
        for w in sentence:
            if self._is_censored(w):
                logger.debug(f"word in sentence: {w[0]}***{w[-1]} is censored. escaping.")
                return None
        final = "".join(sentence)
        return final

    def learn(self, body: str, num_context: int = 1) -> None:
        """
        Lines should be cleaned (filter_message()) before passing
        to this.
        """

        def learn_line(body: str, num_context: int) -> None:
            """
            Learn from a sentence.
            nb: there is a closure here...
            """
            logger.debug("entering learn_line")
            if nltk:
                words = nltk.word_tokenize(body)
            else:
                words = body.split()
            # Ignore sentences of < 1 words XXX was <3
            if len(words) < 1:
                return

            # voyelles = "aÃ Ã¢eÃ©Ã¨ÃªiÃ®Ã¯oÃ¶Ã´uÃ¼Ã»y"
            voyelles = "aeiouy"
            logger.debug("reply:learn_line:words: %s", words)
            for x in range(0, len(words)):

                nb_voy = 0
                digit = 0
                char = 0
                for c in words[x]:
                    if c in voyelles:
                        nb_voy += 1
                    if c.isalpha():
                        char += 1
                    if c.isdigit():
                        digit += 1

                for censored in self.settings.censored:
                    if re.search(censored, words[x]):
                        logger.debug("word: %s***%s is censored. escaping.", words[x][0], words[x][-1])
                        return
                if len(words[x]) > 13 \
                        or (((nb_voy * 100) / len(words[x]) < 26) and len(words[x]) > 5) \
                        or (char and digit) \
                        or (words[x] in self.words) == 0 and self.settings.learning == 0:
                    # if one word as more than 13 characters, don't learn
                    # (in french, this represent 12% of the words)
                    # and d'ont learn words where there are less than 25% of voyels
                    # don't learn the sentence if one word is censored
                    # don't learn too if there are digits and char in the word
                    # same if learning is off
                    logger.debug("reply:learn_line: Bailing because reasons?")
                    return
                elif ("-" in words[x] or "_" in words[x]):
                    words[x] = "#nick"

            num_w = self.settings.num_words
            if num_w != 0:
                num_cpw = self.settings.num_contexts / float(num_w)  # contexts per word
            else:
                num_cpw = 0

            cleanbody = " ".join(words)

            # Hash collisions we don't care about. 2^32 is big :-)
            # Ok so this takes a bytes object... in python3 thats a pain
            cleanbody_b = bytes(cleanbody, "utf-8")
            # ok so crc32 got changed in 3...
            hashval = crc32(cleanbody_b) & 0xffffffff

            logger.debug(hashval)
            # Check context isn't already known
            if hashval not in self.lines:
                if not (num_cpw > 100 and self.settings.learning == 0):
                    self.lines[hashval] = [cleanbody, num_context]
                    # Add link for each word
                    for i, word in enumerate(words):
                        if word in self.words:
                            # Add entry. (line number, word number)
                            self.words[word].append({"hashval": hashval, "index": i})
                        else:
                            self.words[word] = [{"hashval": hashval, "index": i}]
                            self.settings.num_words += 1
                        self.settings.num_contexts += 1
            else:
                self.lines[hashval][1] += num_context

            # if max_words reached, don't learn more
            if self.settings.num_words >= self.settings.max_words:
                self.settings.learning = False

        # Split body text into sentences and parse them
        # one by one.
        body += " "
        logger.debug("reply:replying to %s", body)
        # map ( (lambda x : learn_line(self, x, num_context)), body.split(". "))
        for part in body.split('. '):
            learn_line(part, num_context)
