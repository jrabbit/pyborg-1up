Changes
=======

Changelog summaries; for past changes check `the github releases <https://github.com/jrabbit/pyborg-1up/releases>`_


2.1 (Planned)
-------------
- new client module base class


2.0.1 (Next)
------------


2.0
---

- Dropped python 2 support
- async http client use in discord module
- api rewrite, optional v1 bridge class for old style compat w/ the class formerly known as pyborg's new internals
- discord server management commands
- discord prefix configurable in discord.toml config. use key :kbd:`[discord][prefix]` default is still :kbd:`!`
- new package depenency extras: :kbd:`nlp`, :kbd:`subtitles`, :kbd:`systemd`, :kbd:`graphing` (experimental/in development)
- uses poetry for package lifecycle management
- coverage reporting fixed
- `stronger tokenizer <https://www.nltk.org/api/nltk.tokenize.html#module-nltk.tokenize.casual>`_ more tuned for internet text
- mastodon toml config fields normalized to :kbd:`[pyborg][multiplex_server]`, :kbd:`[pyborg][multiplex_port]`
- :ghpull:`113` added optional random reply rate for discord module use :kbd:`[discord][reply_chance]` in the discord.toml config.
- :ghpull:`114` add option for supplying a nickserv password on irc use :kbd:`[server][nickserv_password]` in your irc.toml config file.
- :ghpull:`119` IRC modules gains support for supplying a server password; use :kbd:`[server][password]` in your irc.toml config file.
- :ghpull:`105` sub comamnd http uses the standardized :kbd:`--brain_name` option now
- systemd extra to support systemd `service daemon notify <https://www.freedesktop.org/software/systemd/man/systemd-notify.html>`_ in the http server.
- new :py:class:`pyborg.pyborg.ExpermientalPyborg` class. an api rework of :py:class:`pyborg.pyborg.pyborg`
- dropped 3.6 support for packaging reasons.

1.4.0
------------

- Added nickname plaintext pings in discord module.
- Discord.py 1.0 support (allows 3.7+ support in pyborg)
- `toml <https://github.com/toml-lang/toml>`_ config files. They live in your pyborg conf folder and there's one for most modules. And one for pyborg's core options. These replace the old cfg files.
- Proper python 3 deps in `PEP508 <https://www.python.org/dev/peps/pep-0508/>`_ compliant specifications in the setup.py. This'll make pypi installs easier on py3.
