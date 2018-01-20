import logging
import time

import arrow
import lxml.html
import requests
import toml
from mastodon import Mastodon

logger = logging.getLogger(__name__)

class PyborgMastodon(object):
    """docstring for PyborgMastodon"""
    def __init__(self, conf_file):
        super(PyborgMastodon, self).__init__()
        self.toml_file = conf_file
        self.settings = toml.load(conf_file)
        self.last_look = arrow.get(self.settings['mastodon']['last_look'])
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']

    def teardown(self):
        self.settings['mastodon']['last_look'] = self.last_look
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
        if not self.multiplexing:
            self.pyborg.save_all()
    
    def learn(self, body):
        if self.multiplexing:
            ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": body})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()
        else:
            self.pyborg.learn(body)

    def reply(self, body):
        if self.multiplexing:
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
        else:
            return self.pyborg.reply(body)

    def should_reply_direct(self, usern):
        should_reply = []
        should_reply.extend([a['acct'] for a in self.mastodon.account_followers(self.my_id)]) # is this cached?
        return usern in should_reply

    def is_reply_to_me(self, item):
        try:
            if item["in_reply_to_account_id"] == self.my_id:
                return True
            else:
                return False
        except KeyError:
            return False

    def start(self):
        self.mastodon = Mastodon(
            client_id = 'pyborg_mastodon_clientcred.secret',
            access_token = 'pyborg_mastodon_usercred.secret',
            api_base_url = self.settings['mastodon']['base_url']
        )
        self.my_id = self.mastodon.account_verify_credentials()['id']

        while True:
            tl = self.mastodon.timeline()
            toots = []
            toots.extend(tl, mentions)
            self.last_look = arrow.utcnow()
            for item in tl:
                if arrow.get(item["created_at"]) > self.last_look and item["acctount"]["id"] is not self.my_id:
                    logger.debug("Got New Toot: {}".format(item))
                    fromacct = item['account']['acct'] # to check if we've banned them?
                    parsed_html = lxml.html.fromstring(item['content'])
                    body = parsed_html.text_content()
                    if self.settings['pyborg']['learning']:
                        self.learn(body)
                    reply = self.reply(body)
                    if reply and (self.should_reply_direct(fromacct) or self.is_reply_to_me(item)):
                        self.mastodon.status_post(reply, in_reply_to_id=item['id'])
                    else:
                        logger.info("Couldn't toot.")
            time.sleep(self.settings['mastodon']['cooldown'])

