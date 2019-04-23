import logging
import time
from typing import Union


import aeidon  # https://github.com/otsaloma/gaupol/tree/master/aeidon
import attr
import requests
import toml

logger = logging.getLogger(__name__)


@attr.s
class PyborgSubtitles(object):
    conf_file = attr.ib()
    subs_file = attr.ib()
    paused = attr.ib(default=False)
    riffs = attr.ib(default=dict(), type=dict)
    pre_processed = attr.ib(default=False)

    # def __attrs_post_init__(self):
    #    pass

    def start(self) -> None:
        self.settings = toml.load(self.conf_file)
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']

        self.project = aeidon.Project()
        logger.debug("About to load subs.")
        self.project.open_main(self.subs_file)
        logger.debug("Loaded subs!")
        self.subtitles = self.project.subtitles
        self.run()

    def clean(self, subtitle: str) -> str:
        text = subtitle.replace(r"{\i1}", "").replace(r"{\i0}", "")
        return text

    def run(self) -> None:
        """As time goes on print out our riffs"""
        for idx, subtitle in enumerate(self.subtitles):
            # remove italics markup
            text = self.clean(subtitle.main_text)

            if text.startswith("("):
                # Should we respond to sound effects?
                print(text)
            else:
                print(text)
                if self.pre_processed:
                    print(">", self.riffs[idx])
                else:
                    print(">", self.reply(text))
            time.sleep(subtitle.duration_seconds)

        self.teardown()

    def pre_process(self) -> None:
        for i, sub in enumerate(self.subtitles):
            reply = self.reply(self.clean(sub.main_text))
            if reply:
                self.riffs[i] = reply

    def reply(self, body) -> Union[str, None]:
        """thin wrapper for reply to switch to multiplex mode"""
        if self.multiplexing:
            ret = requests.post("http://{}:2001/reply".format(self.multi_server), data={"body": body})
            if ret.status_code == requests.codes.ok:
                reply = ret.text
                logger.debug("got reply: %s", reply)
            elif ret.status_code > 499:
                logger.error("Error: Internal Server Error in pyborg_http. see logs.")
                return None
            else:
                ret.raise_for_status()
            return reply
        else:
            raise NotImplementedError

    def teardown(self) -> None:
        pass


if __name__ == '__main__':
    subs = PyborgSubtitles(conf_file="subtitles.toml", subs_file="/home/jack/subs.ssa")
    subs.start()
