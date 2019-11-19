Pyborg is a markov chain bot for many protocols (Discord, IRC, Twitter, etc.) that generates replies based on messages and it's database.

![PyPI](https://img.shields.io/pypi/v/pyborg?style=for-the-badge)![PyPI](https://img.shields.io/pypi/v/pyborg?style=for-the-badge)
[![codecov status](https://codecov.io/gh/jrabbit/pyborg-1up/branch/master/graph/badge.svg)](https://codecov.io/gh/jrabbit/pyborg-1up)
[![CI status](https://travis-ci.org/jrabbit/pyborg-1up.svg)](https://travis-ci.org/jrabbit/pyborg-1up)
[![Documentation Status](https://readthedocs.org/projects/pyborg/badge/?version=latest)](https://pyborg.readthedocs.io/en/latest/?badge=latest)

Install
--------
We're on the cheeseshop! Yay!

`pip install pyborg`

If you want the latest git via pip you'll need to install it via [poetry.](https://poetry.eustace.io/docs/)

Testing releases can be found via:

`pip install --pre pyborg`


Note that we're using Python 3.6+ (for fancy type declarations).

Python 2 support was [dropped with](https://pythonclock.org/) the release of pyborg 2.0.


There are two extras "nlp" and "subtitles". e.g. `pip install pyborg[nlp]`


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

Pyborg can use nltk tagging and tokenizing when installed and configured. Tagging requires `averaged_perceptron_tagger` and tokenization requires `punkt`.
