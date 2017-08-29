import datetime
import logging
import time

import aeidon  # https://github.com/otsaloma/gaupol/tree/master/aeidon
import attr
import toml

logger = logging.getLogger(__name__)

@attr.s
class PyborgSubtitles(object):
    conf_file = attr.ib()
    subs_file = attr.ib()

    # def __attrs_post_init__(self):
    #    pass

    def start(self):
        self.settings = toml.load(self.conf_file)
        self.multiplexing = True
        self.multi_server = self.settings['pyborg']['multi_server']

        self.project = aeidon.Project()
        logger.debug("About to load subs.")
        self.project.open_main(self.subs_file)
        logger.debug("Loaded subs!")
        self.subtitles = self.project.subtitles
        self.run()

    def run(self):
        """As time goes on print out our riffs"""
        for subtitle in self.subtitles:
            # remove italics markup
            text = subtitle.main_text.replace("{\i1}", "").replace("{\i0}", "")
        
            if text.startswith("("):
                # Should we respond to sound effects?
                pass
            else:
                print(text)
            time.sleep(subtitle.duration_seconds)
        
        self.teardown()

    def teardown(self):
        pass


if __name__ == '__main__':
    subs = PyborgSubtitles(conf_file="subtitles.toml", subs_file="/home/jack/subs.ssa")
    subs.start()
