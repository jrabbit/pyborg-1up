import fileinput

import attr
import requests

from pyborg import pyborg


@attr.s
class ModFileIn(object):
    multiplexing = attr.ib()
    multi_server = attr.ib(default="localhost")

    def __attrs_post_init__(self):
        if not self.multiplexing:
            self.pyborg = pyborg.pyborg()

    def run(self, f_name):
        if self.multiplexing:
            ret = requests.get("http://{}:2001/words.json".format(self.multi_server))
            ret.raise_for_status()
            words = ret.json()
        else:
            words = {"words": len(self.pyborg.words), "lines":len(self.pyborg.lines)}
        print("I knew {} words ({} lines) before reading {}".format(words['words'], words['lines'], f_name))
        counter = 0
        for line in fileinput.input(f_name):
            counter = counter + 1
            try:
                self.learn(line)
                
            except KeyboardInterrupt:
                self.save()
                print("Premature termination :-(")

            if counter > 1000000:
                self.save()
                counter = 0
        if self.multiplexing:
            ret2 = requests.get("http://{}:2001/words.json".format(self.multi_server))
            ret2.raise_for_status()
            words = ret2.json()
        else:
            words = {"words": len(self.pyborg.words), "lines":len(self.pyborg.lines)}
        print("I know {} words ({} lines) now.".format(words['words'], words['lines']))

    def learn(self, msg):
        if not self.multiplexing:
            self.pyborg.learn(msg)
        else:
            ret = requests.post("http://{}:2001/learn".format(self.multi_server), data={"body": msg})
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

    def save(self):
        if not self.multiplexing:
            self.pyborg.save_all()
        else:
            ret = requests.post("http://{}:2001/learn".format(self.multi_server))
            if ret.status_code > 499:
                logger.error("Internal Server Error in pyborg_http. see logs.")
            else:
                ret.raise_for_status()

