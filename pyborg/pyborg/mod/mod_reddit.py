#
# PyBorg reddit file input module
#
# Copyright (c) 2000, 2006, 2010-2019 Tom Morton, Sebastien Dailly, Jrabbit
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
import time

import attr
import arrow
import praw
import requests
import six
import toml
from typing import MutableMapping

from pyborg import pyborg
from pyborg.util.hate_filter import SUBREDDIT_HATE_LIST

logger = logging.getLogger(__name__)


@attr.s
class PyborgReddit():
    """Takes a toml config file path"""

    CHUNKING: int = attr.ib(default=100)
    toml_file = attr.ib(default="reddit.toml")
    settings: MutableMapping = attr.ib(init=False)
    multiplexing: bool = attr.ib(init=False)
    multi_server: str = attr.ib(init=False)
    hate_filter_off: bool = attr.ib(init=False)
    auth_app_id: str = attr.ib(init=False)
    auth_script_secret: str = attr.ib(init=False)
    reddit: praw.Reddit = attr.ib(init=False)

    def __init__(self, toml_file="reddit.toml"):
        self.toml_file = toml_file
        self.settings = toml.load(toml_file)

        self.last_look = arrow.get(self.settings['reddit']['last_look'])
        self.multiplexing = self.settings['pyborg']['multiplex']
        if self.multiplexing:
            self.multi_server = self.settings['pyborg']['multiplex_server']

        self.hate_filter_off = self.settings['reddit']['hate_filter_disable']

        # script setup, ideal because no oauth browser rigamarole
        self.auth_app_id = self.settings['reddit']['app_id']
        self.auth_script_secret = self.settings['reddit']['script_secret']

        self.reddit = praw.Reddit(client_id=self.auth_app_id,
                                  client_secret=self.auth_script_secret,
                                  user_agent='pyborg for reddit/0.0.4 pyborg/2.0.0')

        if not self.multiplexing:
            self.pyborg = pyborg.pyborg()
        else:
            self.pyborg = None

    def load_praw_comments(self):
        "Pulls comment objects from reddit using our praw instance"
        # logger.debug("entering load_praw_comments")
        listing = self.reddit.get("/comments.json", params={"limit": self.CHUNKING})
        new_posts = [item for item in listing if arrow.get(item.created_utc) > self.last_look]
        self.last_look = arrow.utcnow()
        logger.debug("loaded %s new comments", len(new_posts))
        return new_posts

    def handle_post(self, post):
        # logger.debug("entering handle_post")
        if six.PY2:
            post_extract = post.body.encode('utf8')
        else:
            post_extract = post.body
        if self.settings['reddit']['learning']:
            if not self.multiplexing:
                # print(post_extract)
                # post_clean = pyborg.filter_message(post.body, self.pyborg) # this expects a clean ascii string?
                logger.debug(post_extract)
                self.pyborg.learn(post_extract)
            else:
                ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": post_extract})
                if ret.status_code > 499:
                    logger.error("Internal Server Error in pyborg_http. see logs.")
                else:
                    ret.raise_for_status()
        # replies not supported yet!

    def post_is_clean(self, post):
        # logger.debug("entered post_is_clean")
        if post.subreddit.display_name in SUBREDDIT_HATE_LIST:
            return False
        return True

    def start(self):
        # print("I knew {} words ({} lines) before reading Reddit.com".format(self.pyborg.settings.num_words, len(self.pyborg.lines)))
        # this doesn't work on multiplexing
        while True:
            new_posts = self.load_praw_comments()
            for post in new_posts:
                if self.hate_filter_off:
                    logger.info("help me")
                    self.handle_post(post)
                elif self.post_is_clean(post):
                    self.handle_post(post)
                else:
                    logger.info("Excluding comment from filtered subreddit")
            time.sleep(self.settings['reddit']['cooldown'])

    def teardown(self):
        self.settings['reddit']['last_look'] = self.last_look.datetime
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()
            print("I know {} words ({} lines) now.".format(self.pyborg.settings.num_words, len(self.pyborg.lines)))
