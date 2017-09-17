#! /usr/bin/env python

from setuptools import setup

from pyborg import __version__

setup(name="pyborg",
      version=__version__,
      packages=["pyborg", "pyborg.util", "pyborg.mod"],
      scripts=['pyborg-filein.py',
               'pyborg-telnet.py',
               'pyborg-irc.py',
               'pyborg-bigfilein.py',
               'pyborg_experimental.py'],
      author="Jack Laxson",
      author_email="jackjrabbit@gmail.com",
      description="Markov chain bot for irc which generates replies to messages",
      license="GPL v2 or later",
      install_requires=["irc>=15.1.1", "toml",
                        "arrow==0.10.0", "PyTumblr==0.0.6", "requests", "bottle",
                        "venusian", "click", "humanize", "praw", "Mastodon.py", "lxml", "attrs", "statsd"],
      entry_points='''
          [console_scripts]
          pyborg=pyborg_experimental:cli_base
      ''',
      url="https://github.com/jrabbit/pyborg-1up/",
      classifiers=["License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
                   "Topic :: Communications :: Chat :: Internet Relay Chat",
                   "Topic :: Games/Entertainment",
                   "Programming Language :: Python :: 2.7",
                   "Programming Language :: Python :: 3", ])
