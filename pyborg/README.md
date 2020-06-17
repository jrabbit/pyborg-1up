Pyborg is a markov chain bot for many protocols (Discord, IRC, Twitter, etc.) that generates replies based on messages and it's database.

[![PyPI](https://img.shields.io/pypi/v/pyborg)](https://pypi.org/project/pyborg/)
[![codecov](https://codecov.io/gh/jrabbit/pyborg-1up/branch/dev/graph/badge.svg)](https://codecov.io/gh/jrabbit/pyborg-1up)
[![Build Status](https://travis-ci.com/jrabbit/pyborg-1up.svg?branch=dev)](https://travis-ci.com/jrabbit/pyborg-1up)
[![Documentation Status](https://readthedocs.org/projects/pyborg/badge/?version=latest)](https://pyborg.readthedocs.io/en/latest/?badge=latest)

Install
--------
We're on the cheeseshop! Yay!

`pip install pyborg`

If you want the latest version from git you'll need to install the project with [poetry.](https://python-poetry.org/docs/) in the source directory.

Early test/beta releases can be found via:

`pip install --pre pyborg`


Note that we're using Python 3.6+ (for fancy type declarations).

Python 2 support was [dropped with](https://pythonclock.org/) the release of pyborg 2.0.


There are several extras: "nlp", "systemd", "subtitles", "graphing". Some extras may be rather experimental like "graphing" at time of writing.

e.g. `pip install pyborg[nlp]`


Basic Usage
-----------

`pyborg` is our new unified pyborg command line interface.


Documentation
-------------

[Docs can be found on RTD.](http://pyborg.readthedocs.io/en/latest/)


Notes
-----

Pyborg is skipping version 1.3; this was used for a transitory database/"brain" restructuring that was underwhelming. 

Ancient original tarballs were hosted at Gna! which is now gone. [Thankfully Internet Archive has a copy!](https://web.archive.org/web/20170225141934/http://download.gna.org/pyborg/) 

Pyborg was originally developed by Tom Morton and Sébastien Dailly.


Suggested NLTK data
-------------------

Pyborg can use nltk tagging and tokenizing when installed and configured. Tagging requires `averaged_perceptron_tagger` and tokenization requires `punkt`. This needs the `nlp` extra.
