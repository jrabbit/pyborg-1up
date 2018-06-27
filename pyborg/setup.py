#! /usr/bin/env python
import sys

from setuptools import setup

from pyborg import __version__


requires = [
    "irc>=15.1.1",
    "toml",
    "arrow>=0.10.0",
    "PyTumblr==0.0.6",
    "requests",
    "bottle",
    "venusian",
    "click",
    "humanize",
    "praw",
    "Mastodon.py",
    "tweepy",
    "lxml",
    "attrs",
    "statsd",
    "prompt_toolkit",
]
if sys.version_info >= (3,):
    requires.extend(["discord.py", "aeidon"])
setup(
    name="pyborg",
    version=__version__,
    packages=["pyborg", "pyborg.util", "pyborg.mod"],
    scripts=["pyborg_experimental.py"],
    author="Jack Laxson",
    author_email="jackjrabbit@gmail.com",
    description="Markov chain bot for irc which generates replies to messages",
    license="GPL v3 or later",
    install_requires=requires,
    entry_points="""
          [console_scripts]
          pyborg=pyborg_experimental:cli_base
      """,
    url="https://github.com/jrabbit/pyborg-1up/",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "Topic :: Games/Entertainment",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
    ],
)
