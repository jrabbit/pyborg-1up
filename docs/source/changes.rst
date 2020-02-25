Changes
=======

Changelog summaries; for past changes check `the github releases <https://github.com/jrabbit/pyborg-1up/releases>`_

2.0
---

- Dropped python 2 support
- async http client use in discord module
- api rewrite, optional v1 bridge class for old style compat w/ the class formerly known as pyborg's new internals
- discord server management commands
- new package depenency extras: :kbd:`nlp`, :kbd:`subtitles`
- uses poetry for package lifecycle management
- coverage reporting fixed
- `stronger tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.casual>`_ more tuned for internet text
- mastodon toml config fields normalized to :kbd:`[pyborg][multiplex_server]`, :kbd:`[pyborg][multiplex_port]`
- (pr #113) added optional random reply rate for discord module use :kbd:`[discord][reply_chance]` in the discord.toml config.
- (pr #114) add option for supplying a nickserv password on irc use :kbd:`[server][nickserv_password]` in your irc.toml config file.
- sub comamnd http uses the standardized :kbd:`--brain_name` option now (related pr #105)

1.4.0
------------

- Added nickname plaintext pings in discord module.
- Discord.py 1.0 support (allows 3.7+ support in pyborg)
- `toml <https://github.com/toml-lang/toml>`_ config files. They live in your pyborg conf folder and there's one for most modules. And one for pyborg's core options. These replace the old cfg files.
- Proper python 3 deps in `PEP508 <https://www.python.org/dev/peps/pep-0508/>`_ compliant specifications in the setup.py. This'll make pypi installs easier on py3.
