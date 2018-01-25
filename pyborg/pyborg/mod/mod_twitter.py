import logging
import random
import sys
import time

import arrow
import requests
import toml
import tweepy

logger = logging.getLogger(__name__)

class NoBlankLogFilter(logging.Filter):
    def filter(self, record):
        if isinstance(record.args, tuple):
            # logger.info("args: %s", record.args)
            if record.msg == "PARAMS: %r" and record.args[0] == {}:
                logger.debug("ignoring %s", record)
                return 0
            else:
                return True
        else:
            return True

logging.getLogger("tweepy.binder").addFilter(NoBlankLogFilter())

class PyborgTwitter(object):
    def __init__(self, conf_file):
        self.toml_file = conf_file
        self.settings = toml.load(conf_file)
        self.last_look = arrow.get(self.settings['twitter']['last_look'])
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']

    def learn(self, body):
        if self.multiplexing:
            try:
                ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": body})
                if ret.status_code > 499:
                    logger.error("Internal Server Error in pyborg_http. see logs.")
                else:
                    ret.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                logger.exception(e)
                self.teardown()
                sys.exit(7)
        else:
            self.pyborg.learn(body)

    def reply(self, body):
        if self.multiplexing:
            try:
                ret = requests.post("http://{}:2001/reply".format(self.multi_server), data={"body": body})
                if ret.status_code == requests.codes.ok:
                    reply = ret.text
                    logger.debug("got reply: %s", reply)
                elif ret.status_code > 499:
                    logger.error("Internal Server Error in pyborg_http. see logs.")
                    return
                else:
                    ret.raise_for_status()
                return reply
            except requests.exceptions.ConnectionError as e:
                logger.exception(e)
                self.teardown()
                sys.exit(7)
        else:
            return self.pyborg.reply(body)

    def get_tweets(self):
        try:
            public_tweets = self.api.home_timeline()

            return public_tweets
        except tweepy.error.RateLimitError:
            logger.info("Hit rate-limit.")
            return []

    def is_reply_to_me(self, tweet):
        """TODO: determine if we should reply"""
        return False

    def handle_tweet(self, tweet):
        parsed_date = arrow.get(tweet.created_at)
        logger.debug(parsed_date)
        if parsed_date > self.last_look:
            logger.info("Should respond to this tweet: %s from %s", tweet.text, tweet.user.screen_name)
            if self.settings['pyborg']['learning']:
                self.learn(tweet.text)
            reply = self.reply(tweet.text)
            reply = reply.replace("#nick", "@"+tweet.user.screen_name)
            if reply:
                try:
                    if random.choice([True, True, False]) or self.is_reply_to_me(tweet):
                        # auto_populate_reply_metadata 
                        # https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-update
                        self.api.update_status(reply, in_reply_to_status_id=int(tweet.id), auto_populate_reply_metadata=True)
                    else:
                        self.api.update_status(reply)
                except tweepy.error.TweepError as e:
                    # trying to avoid tweepy.error.TweepError: [{'code': 187, 'message': 'Status is a duplicate.'}]
                    logger.exception(e)


    def teardown(self):
        self.settings['twitter']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()

    def start(self):
        auth = tweepy.OAuthHandler(self.settings['twitter']['auth']['consumer_key'], self.settings['twitter']['auth']['consumer_secret'])
        auth.set_access_token(self.settings['twitter']['auth']['access_token'], self.settings['twitter']['auth']['access_token_secret'])

        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        logger.info("Got API, starting twitter module...")
        while True:
            for t in self.get_tweets():
                self.handle_tweet(t)
            self.last_look = arrow.utcnow()
            logger.debug("Sleeping for {} seconds".format(self.settings['twitter']['cooldown']))
            time.sleep(self.settings['twitter']['cooldown'])
