configs = {
    "example.reddit.toml": {"pyborg": {"multiplex": False}, "reddit": {"cooldown": 20, "hate_filter_disable": False, "learning": True}},
    "example.irc.toml": {
        "multiplex": True,
        "multiplex_server": "localhost",
        "nickname": "PyBorg",
        "password": "",
        "quitmsg": "Bye :-(",
        "realname": "Pyborg",
        "reply2ignored": False,
        "server": {
            "channels": [
                {"chan": "#ranarchism", "reply_chance": 5, "speaking": True},
                {"chan": "#queertoo", "reply_chance": 5, "speaking": False},
            ],
            "ignorelist": [],
            "owners": ["jrabbit"],
            "port": 6697,
            "server": "chat.freenode.net",
            "ssl": True,
        },
        "speaking": True,
        "speakingchans": ["#test"],
        "stealth": False,
    },
    "example.tumblr.toml": {
        "auth": {
            "consumer_key": "from tumblr",
            "consumer_secret": "from tumblr",
            "oauth_secret": "from tumblr",
            "oauth_token": "from tumblr",
        },
        "pyborg": {"multiplex": False},
        "tumblr": {"blog": "your-blog.tumblr.com", "cooldown": 20, "ignore": [], "learning": False, "tags": ["your tag"]},
    },
    "example.discord.toml": {"discord": {"learning": True, "plaintext_ping": True}, "pyborg": {"multiplex": True}},
    "example.pyborg.toml": {"censored": [], "max_words": 6000},
    "example.mastodon.toml": {
        "mastodon": {"base_url": "https://botsin.space", "cooldown": 20, "pyborg": {"multiplexing_server": "localhost"}}
    },
}
