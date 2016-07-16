#!/usr/bin/env python
import time
import sys
import logging

import arrow
import baker
import pytumblr
import toml

import pyborg.pyborg

logger = logging.getLogger(__name__)

class PyborgTumblr(object):

    """Takes a toml config file path and a pyborg.pyborg.pyborg instance."""

    def __init__(self, toml_file):
        self.toml_file = toml_file
        self.settings = toml.load(toml_file)
        self.client = pytumblr.TumblrRestClient(self.settings['auth']['consumer_key'], 
                                                self.settings['auth']['consumer_secret'], 
                                                self.settings['auth']['oauth_token'], 
                                                self.settings['auth']['oauth_secret'])
        self.last_look = arrow.get(self.settings['tumblr']['last_look'])
        self.multiplexing = self.settings['pyborg']['multiplex']
        if not self.multiplexing:
            self.pyborg = pyborg.pyborg.pyborg()
        else:
            self.pyborg = None

    def load_new_from_tag(self, tag):
        posts = self.client.tagged(tag)
        # setattr(self, "date-%s" %)
        new_posts = filter( lambda x: arrow.get(x['date']) > self.last_look, posts)
        self.last_look = arrow.utcnow()
        logger.debug("loaded new posts")
        return new_posts

    def start(self):
        while True:
            new_posts = self.load_new_from_tag("hello bill")
            for post in new_posts:
                if self.settings['tumblr']['learning']:
                    self.pyborg.learn(post['body'])

                logger.info("found post: \n%s", post['summary'])
                msg =  self.pyborg.reply(post['summary'])
                if msg:
                    logger.info("Reblogging with comment: %s", msg)
                    self.client.reblog(self.settings['tumblr']['blog'], id=post['id'], reblog_key=post['reblog_key'], comment=msg)
                else:
                    logger.info("No comment.")

            time.sleep(self.settings['tumblr']['cooldown'])
    def teardown(self):
        self.settings['tumblr']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()


@baker.command(default=True, shortopts={"toml_conf": "f"})
def start_tumblr_bot(verbose=True, toml_conf="example.tumblr.toml"):
    if verbose:
        logging.basicConfig(level=logging.INFO)
    bot = PyborgTumblr(toml_conf)
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.teardown()
        sys.exit()
    except Exception:
        bot.teardown()
        raise

if __name__ == '__main__':
    baker.run()