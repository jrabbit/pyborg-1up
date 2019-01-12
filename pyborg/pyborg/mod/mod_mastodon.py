import logging
import time
import sys
import os.path
from typing import List, Dict, Optional

import arrow
import lxml.html
import requests
import toml
from mastodon import Mastodon

logger = logging.getLogger(__name__)

class PyborgMastodon(object):
    """it does toots"""

    # todo: attrs
    def __init__(self, conf_file):
        self.toml_file = conf_file
        self.settings = toml.load(conf_file)
        self.last_look = arrow.get(self.settings['mastodon']['last_look'])
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']

    def teardown(self) -> None:
        self.settings['mastodon']['last_look'] = self.last_look.datetime
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            raise NotImplementedError("Use multiplexing.")
            # self.pyborg.save_all()

    def learn(self, body) -> None:
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
                sys.exit(17)
        else:
            raise NotImplementedError("Use multiplexing.")
            # self.pyborg.learn(body)

    def reply(self, body) -> Optional[str]:
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
                logger.exception(e)
                self.teardown()
                sys.exit(17)
        else:
            raise NotImplementedError("use multiplexing.")
            # return self.pyborg.reply(body)

    def should_reply_direct(self, usern) -> bool:
        should_reply = []
        should_reply.extend([a['acct'] for a in self.mastodon.account_followers(self.my_id)])  # is this cached?
        return usern in should_reply

    def is_reply_to_me(self, item: Dict) -> bool:
        logger.debug(item)
        try:
            if item["in_reply_to_account_id"] == self.my_id:
                return True
            elif item["type"] == "mention":
                if any([True for mention in item["status"]["mentions"] if mention['id'] == self.my_id]):
                    return True
                else:
                    # Is this actually possible?
                    return False
            else:
                return False
        except KeyError:
            return False

    def handle_toots(self, toots: List[Dict]) -> None:
        for item in toots:
            # logger.debug(arrow.get(item["created_at"]) > self.last_look)
            logger.debug(item['content'])
            logger.debug(arrow.get(item["created_at"]) - self.last_look)
            if (arrow.get(item["created_at"]) > self.last_look) and item["account"]["id"] is not self.my_id:
                logger.info("Got New Toot: {}".format(item))
                fromacct = item['account']['acct']  # to check if we've banned them?
                parsed_html = lxml.html.fromstring(item['content'])
                body = parsed_html.text_content()
                if self.settings['pyborg']['learning']:
                    self.learn(body)
                reply = self.reply(body)
                if reply and (self.should_reply_direct(fromacct) or self.is_reply_to_me(item)):
                    self.mastodon.status_post(reply, in_reply_to_id=item['id'])
                else:
                    logger.info("Couldn't toot.")

    def start(self, folder=".") -> None:
        "This actually runs the bot"
        self.mastodon = Mastodon(
            client_id=os.path.join(folder, 'pyborg_mastodon_clientcred.secret'),
            access_token=os.path.join(folder, 'pyborg_mastodon_usercred.secret'),
            api_base_url=self.settings['mastodon']['base_url']
        )
        self.my_id = self.mastodon.account_verify_credentials()['id']

        while True:
            tl = self.mastodon.timeline()
            toots: List[Dict] = []
            mentions = [notif['status'] for notif in self.mastodon.notifications() if notif['type'] == "mention"]
            toots.extend(tl)
            toots.extend(mentions)
            self.handle_toots(toots)
            self.last_look = arrow.utcnow()
            logger.debug("Sleeping for {} seconds".format(self.settings['mastodon']['cooldown']))
            time.sleep(self.settings['mastodon']['cooldown'])
