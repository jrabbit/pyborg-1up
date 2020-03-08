import contextlib
import logging
import os.path
import re
import sys
import time
from typing import Any, List, Mapping, MutableMapping, Optional, Sequence, Union, cast

import arrow
import attr
import requests
import toml
from defusedxml.ElementTree import ParseError
from defusedxml.ElementTree import fromstring as defused_from_string
from mastodon import Mastodon

logger = logging.getLogger(__name__)

# mypy typing hints
# https://mastodonpy.readthedocs.io/en/stable/#notification-dicts
NotificationDict = Mapping[str, Union[str, Mapping[str, Any]]]
# https://mastodonpy.readthedocs.io/en/stable/#toot-dicts
TootDict = Mapping[str, Union[bool, Mapping[str, Any], str, Sequence]]
ManyToot = List[Union[NotificationDict, TootDict]]

NO_BOT = re.compile("#nobot")


@attr.s
class PyborgMastodon:
    """it does toots"""

    toml_file: str = attr.ib()
    settings: MutableMapping[str, Any] = attr.ib(default=None)
    last_look: arrow.Arrow = attr.ib(default=None)
    multiplexing: bool = attr.ib(default=True)
    multi_server: str = attr.ib(default="localhost")
    multi_port: int = attr.ib(default=2001)
    mastodon: Mastodon = attr.ib(init=False)
    my_id: int = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.settings = toml.load(self.toml_file)
        with contextlib.suppress(KeyError):
            self.last_look = arrow.get(self.settings["mastodon"]["last_look"])
            self.multi_server = self.settings["pyborg"]["multiplex_server"]
            self.multi_port = self.settings["pyborg"]["multiplex_port"]

    def teardown(self) -> None:
        self.settings["mastodon"]["last_look"] = self.last_look.datetime
        with open(self.toml_file, "w") as f:
            toml.dump(self.settings, f)
            logging.info("saved mastodon config at: %s", self.toml_file)
        if not self.multiplexing:
            raise NotImplementedError("Use multiplexing.")
            # self.pyborg.save_all()

    def learn(self, body: str) -> None:
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

    def reply(self, body: str) -> Optional[str]:
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

    def should_reply_direct(self, usern: str) -> bool:
        should_reply = []
        should_reply.extend([a["acct"] for a in self.mastodon.account_followers(self.my_id)])  # is this cached?
        return usern in should_reply

    def is_reply_to_me(self, item: Union[NotificationDict, TootDict]) -> bool:
        logger.debug(item)
        try:
            our_id = cast(int, item["in_reply_to_account_id"])
            return our_id == self.my_id
        except KeyError:
            if item["type"] == "mention":
                mentions = cast(Sequence, item["mentions"])
                return any([True for mention in mentions if mention["id"] == self.my_id])
            else:
                return False

    def toot_has_cw(self, toot: Union[NotificationDict, TootDict]) -> bool:
        return cast(bool, toot["sensitive"])

    def user_has_nobot(self, toot: Union[NotificationDict, TootDict]) -> bool:
        return cast(bool, NO_BOT.match(cast(Mapping, toot["account"])["note"]))

    def handle_toots(self, toots: ManyToot) -> None:
        for item in toots:
            # logger.debug(arrow.get(item["created_at"]) > self.last_look)
            logger.debug(item["content"])
            logger.debug(arrow.get(item["created_at"]) - self.last_look)
            if (arrow.get(item["created_at"]) > self.last_look) and cast(Mapping, item["account"])["id"] is not self.my_id:
                # its new, does it have CW? if so, skip, if user has #nobot, skip
                if self.toot_has_cw(item):
                    continue
                if self.user_has_nobot(item):
                    continue
                logger.info("Got New Toot: {}".format(item))
                fromacct = cast(Mapping, item["account"])["acct"]  # to check if we've banned them?
                try:
                    etree = defused_from_string(item["content"])
                    body = etree.text
                    # will this work always??
                    logger.debug(f"got body: {body}")

                    if self.settings["pyborg"].get("learning", True):
                        self.learn(body)

                    reply = self.reply(body)

                    if reply:
                        logger.debug("got reply from http: %s", reply)
                        if self.should_reply_direct(fromacct) or self.is_reply_to_me(item):
                            self.mastodon.status_post(reply, in_reply_to_id=item["id"])
                        else:
                            logger.info("Got reply but declined to toot. recv'd body: %s", body)
                    else:
                        logger.info("Couldn't toot.")
                except ParseError:
                    logging.exception(f"couldn't parse: {item['content']}")

    def start(self, folder: str = ".") -> None:
        "This actually runs the bot"
        self.mastodon = Mastodon(
            client_id=os.path.join(folder, "pyborg_mastodon_clientcred.secret"),
            access_token=os.path.join(folder, "pyborg_mastodon_usercred.secret"),
            api_base_url=self.settings["mastodon"]["base_url"],
        )
        self.my_id = self.mastodon.account_verify_credentials()["id"]

        while True:
            tl = self.mastodon.timeline()
            toots: ManyToot = list()
            mentions = [notif["status"] for notif in self.mastodon.notifications() if notif["type"] == "mention"]
            toots.extend(tl)
            toots.extend(mentions)
            self.handle_toots(toots)
            self.last_look = arrow.utcnow()
            logger.debug("Sleeping for {} seconds".format(self.settings["mastodon"]["cooldown"]))
            time.sleep(self.settings["mastodon"]["cooldown"])
