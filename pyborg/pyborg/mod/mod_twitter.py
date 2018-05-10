import logging
import random
import sys
import time
from typing import List, Union, Dict

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

# def follow_user_cli(api:tweepy.API, target_user: str) -> None:
#     api.create_friendship(target_user)


class PyborgTwitter(object):
    def __init__(self, conf_file):
        self.toml_file = conf_file
        self.settings: Dict = toml.load(conf_file)
        self.last_look = arrow.get(self.settings['twitter']['last_look'])
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']
        self.pyborg = None

    def learn(self, body: str) -> None:
        if self.multiplexing:
            try:
                ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": body})
                if ret.status_code > 499:
                    logger.error("Internal Server Error in pyborg_http. see logs.")
                else:
                    ret.raise_for_status()
            except requests.exceptions.ConnectionError as e:
                logger.exception(str(e))
                self.teardown()
                sys.exit(7)
        else:
            self.pyborg.learn(body)

    def reply(self, body) -> Union[str, None]:
        if self.multiplexing:
            try:
                ret = requests.post("http://{}:2001/reply".format(self.multi_server), data={"body": body})
                if ret.status_code == requests.codes.ok:
                    reply = ret.text
                    logger.debug("got reply: %s", reply)
                elif ret.status_code > 499:
                    logger.error("Internal Server Error in pyborg_http. see logs.")
                    return None
                else:
                    ret.raise_for_status()
                return reply
            except requests.exceptions.ConnectionError as e:
                logger.exception(str(e))
                self.teardown()
                sys.exit(7)
        else:
            return self.pyborg.reply(body)

    def get_tweets(self) -> List[tweepy.Status]:
        try:
            public_tweets = self.api.home_timeline()
            return public_tweets
        except tweepy.error.RateLimitError:
            logger.info("Hit rate-limit.")
        except ConnectionError as e:
            logger.info("ConnectionError: %s", e)
        except tweepy.error.TweepError as e:
            logger.info("Other TweepyError: %s", e)
        return []

    def is_reply_to_me(self, tweet: tweepy.Status) -> bool:
        me_at = self.me.screen_name
        if me_at in [x["screen_name"] for x in tweet.entities["user_mentions"]] or tweet.in_reply_to_user_id == self.me.id:
            logger.debug("I'm mentioned in: %s or am being replied to?", tweet.entities["user_mentions"])
            return True
        else:
            return False

    def _bail_if_only_images(self, tweet: tweepy.Status) -> bool:
        # [x["indices"] for x in s.extended_entities["media"]]
        # AttributeError: 'Status' object has no attribute 'extended_entities'
        full = len(tweet.text)
        try:
            indices = [x["indices"] for x in tweet.extended_entities["media"]]
            for idx_start, idx_end in indices:
                full =- (idx_end - idx_start)  # noqa WHY THE FUCK
            if full == 0:
                return True
            else:
                return False
        except AttributeError:
            return False
        except Exception:
            logger.exception("Error in _bail_if_only_images")
            return False

    def handle_tweet(self, tweet: tweepy.Status) -> None:
        parsed_date = arrow.get(tweet.created_at)
        logger.debug(parsed_date)
        if parsed_date > self.last_look:
            logger.info("Should respond to this tweet: %s from %s", tweet.text, tweet.user.screen_name)
            # remove literal RTs here
            if tweet.text.startswith("RT"):
                text = tweet.text[3:]
            else:
                text = tweet.text
            # if hasattr(tweet, "quote_tweet"):
            # doesn't actually get the full quote tweet??? so fuck that
            if self._bail_if_only_images(tweet):
                return
            tweete_list = list()
            for x in text.split():
                if x.startswith("@"):
                    x = "#nick"
                tweete_list.append(x)
            logger.debug(str(tweete_list))
            line = " ".join(tweete_list)
            if self.settings['pyborg']['learning']:
                self.learn(line)
            reply = self.reply(line)
            if reply == "#nick":
                return
            if reply:
                reply = reply.replace("#nick", "@" + tweet.user.screen_name)
                try:
                    if random.choice([True, False, False]) or self.is_reply_to_me(tweet):
                        # auto_populate_reply_metadata
                        # https://developer.twitter.com/en/docs/tweets/post-and-engage/api-reference/post-statuses-update
                        self.api.update_status(reply, in_reply_to_status_id=int(tweet.id), auto_populate_reply_metadata=True)
                    else:
                        self.api.update_status(reply)
                except tweepy.error.TweepError as e:
                    # trying to avoid tweepy.error.TweepError: [{'code': 187, 'message': 'Status is a duplicate.'}]
                    logger.exception(e)

    def teardown(self) -> None:
        self.settings['twitter']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()

    def start(self) -> None:
        auth = tweepy.OAuthHandler(self.settings['twitter']['auth']['consumer_key'], self.settings['twitter']['auth']['consumer_secret'])
        auth.set_access_token(self.settings['twitter']['auth']['access_token'], self.settings['twitter']['auth']['access_token_secret'])

        self.api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
        self.me = self.api.me()
        logger.info("Got API, starting twitter module...")
        while True:
            for t in self.get_tweets():
                self.handle_tweet(t)
            self.last_look = arrow.utcnow()
            logger.debug("Sleeping for {} seconds".format(self.settings['twitter']['cooldown']))
            time.sleep(self.settings['twitter']['cooldown'])
