import time
import sys
import logging

import arrow
import baker
import pytumblr
import toml

import pyborg.pyborg

class PyborgTumblr(object):

    """Takes a toml config file path and a pyborg.pyborg.pyborg instance."""

    def __init__(self, toml_file, pyb):
        self.toml_file = toml_file
        self.settings = toml.load(toml_file)
        self.client = pytumblr.TumblrRestClient(self.settings['auth']['consumer_key'], 
                                                self.settings['auth']['consumer_secret'], 
                                                self.settings['auth']['oauth_token'], 
                                                self.settings['auth']['oauth_secret'])
        self.last_look = arrow.get(self.settings['tumblr']['last_look'])
        self.pyborg = pyb

    def load_new_from_tag(self, tag):
        posts = self.client.tagged(tag)
        # setattr(self, "date-%s" %)
        new_posts = filter( lambda x: arrow.get(x['date']) > self.last_look, posts)
        self.last_look = arrow.utcnow()
        logging.debug("loaded new posts")
        return new_posts

    def start(self):
        while True:
            new_posts = self.load_new_from_tag("hello bill")
            for post in new_posts:
                if self.settings['tumblr']['learning']:
                    self.pyborg.learn(post['body'])

                logging.info("found post: \n%s", post['summary'])
                msg =  self.pyborg.reply(post['summary'])
                if msg:
                    logging.info("Reblogging with comment: %s", msg)
                    self.client.reblog(self.settings['tumblr']['blog'], id=post['id'], reblog_key=post['reblog_key'], comment=msg)
                else:
                    logging.info("No comment.")

            time.sleep(self.settings['tumblr']['cooldown'])
    def teardown(self):
        self.settings['tumblr']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)


@baker.command(default=True)
def start_irc_bot(verbose=True):
    if verbose:
        logging.basicConfig(level=logging.INFO)
    pyb = pyborg.pyborg.pyborg()
    bot = PyborgTumblr("example.tumblr.toml", pyb)
    try:
        bot.start()
    except KeyboardInterrupt:
        pyb.save_all()
        bot.teardown()
        sys.exit()
    except Exception:
        pyb.save_all()
        raise

if __name__ == '__main__':
    baker.run()