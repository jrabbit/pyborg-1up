#! /usr/bin/env python
import glob
from os import path

from setuptools import setup

from pyborg import __version__


this_directory = path.abspath(path.dirname(__file__))

with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

requires = [
    "irc",
    "toml",
    "arrow",
    "PyTumblr",
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
    "discord.py",
    "aeidon",
]
setup(
    name="pyborg",
    version=__version__,
    packages=["pyborg", "pyborg.util", "pyborg.mod"],
    scripts=["pyborg_entrypoint.py"],
    author="Jack Laxson",
    author_email="jackjrabbit@gmail.com",
    description="Markov chain bot for many protocols (discord, irc, twitter, mastodon, file, linein) which generates replies to messages",
    long_description=long_description,
    long_description_content_type='text/markdown',
    license="GPL v3 or later",
    install_requires=requires,
    data_files=[('share/pyborg/example_conf', glob.glob("example.*.toml"))],
    entry_points="""
          [console_scripts]
          pyborg=pyborg_entrypoint:cli_base
      """,
    url="https://github.com/jrabbit/pyborg-1up/",
    classifiers=[
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Topic :: Communications :: Chat :: Internet Relay Chat",
        "Topic :: Games/Entertainment",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ],
)
