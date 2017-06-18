import toml
import logging
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


    def teardown(self):
        pass
    
    def start(self):
        mastodon = Mastodon(
            client_id = 'pyborg_mastodon_clientcred.secret',
            access_token = 'pyborg_mastodon_usercred.secret',
            api_base_url = self.settings['mastodon']['base_url']
        )
        mastodon.toot('Tooting from python using #mastodonpy !')