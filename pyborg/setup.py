#! /usr/bin/env python

from setuptools import setup
setup(name="pyborg",
      version="1.3.0b1",
      packages=["pyborg", "pyborg.util", "pyborg.mod"],
      scripts=['pyborg-filein.py',
               'pyborg-telnet.py',
               'pyborg-irc.py',
               'pyborg-bigfilein.py',
               'pyborg_tumblr.py',
               'pyborg_experimental.py'],
      author="Jack Laxson",
      author_email="jackjrabbit@gmail.com",
      description="Markov chain bot for irc which generates replies to messages",
      license="GPL v2 or later",
      install_requires=["irc==15.1.1", "toml", "baker==1.3",
                        "arrow==0.10.0", "PyTumblr==0.0.6", "requests", "bottle",
                        "venusian", "click"],
      entry_points='''
          [console_scripts]
          pyborg=pyborg_experimental:cli_base
      ''',
      url="https://github.com/jrabbit/pyborg-1up/",
      classifiers=["License :: OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
                   "Topic :: Communications :: Chat :: Internet Relay Chat",
                   "Topic :: Games/Entertainment"])
