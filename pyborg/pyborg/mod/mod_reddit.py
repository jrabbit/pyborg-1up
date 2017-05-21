#
# PyBorg reddit file input module
#
# Copyright (c) 2000, 2006, 2010-2017 Tom Morton, Sebastien Dailly, Jrabbit
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
import string
import sys
import requests
import json
import time
import logging
import arrow
import baker
import toml

from pyborg import pyborg

logger = logging.getLogger(__name__)

class PyborgReddit(object):

    """Takes a toml config file path"""

    def __init__(self, toml_file="pyborg.reddit.toml"):
        self.toml_file = toml_file
        self.settings = toml.load(toml_file)

        self.last_look = arrow.get(self.settings['reddit']['last_look'])
        self.multiplexing = self.settings['pyborg']['multiplex']
        self.url = 'http://www.reddit.com/comments.json?limit=100'
        self.headers = {'user-agent': 'pyborg for reddit/0.0.2 pyborg/1.3.0'}

        if not self.multiplexing:
            self.pyborg = pyborg.pyborg()
        else:
            self.pyborg = None

    def load_new_comments(self):
        ret = requests.get(self.url, headers=self.headers)
        ret.raise_for_status()
        js = ret.json()
        comments = js['data']['children']
        print(comments[0])
        new_posts = filter( lambda x: arrow.get(x['data']['created_utc']) > self.last_look, comments)
        self.last_look = arrow.utcnow()
        logger.debug("loaded new comments")
        return new_posts

    def handle_post(self, post):
        if self.settings['reddit']['learning']:
            if not self.multiplexing:
                post_extract = post['data']['body'].encode('utf8')
                post_clean = pyborg.filter_message(post_extract, self.pyborg) # this expects a clean ascii string?
                self.pyborg.learn(post_clean)
            else:
                raise NotImplementedError

        # replies not supported yet!
    def start(self):
        print("I knew {} words ({} lines) before reading Reddit.com".format(self.pyborg.settings.num_words, len(self.pyborg.lines)))
        while True:
            new_posts = self.load_new_comments()
            for post in new_posts:
                self.handle_post(post)
            time.sleep(self.settings['reddit']['cooldown'])

    def teardown(self):
        self.settings['reddit']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()
            print("I know {} words ({} lines) now.".format(self.pyborg.settings.num_words, len(self.pyborg.lines)))

