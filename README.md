Pyborg is a markov chain bot for irc that generates replies based on messages and it's database.


[![codecov](https://codecov.io/gh/jrabbit/pyborg-1up/branch/master/graph/badge.svg)](https://codecov.io/gh/jrabbit/pyborg-1up)
[![CIstatus](https://travis-ci.org/jrabbit/pyborg-1up.svg)](https://travis-ci.org/jrabbit/pyborg-1up)

Install
--------
We're on the cheeseshop! Yay!

`pip install pyborg`

If you want the latest git via pip you'll need some special sauce.

`pip install -e git+https://github.com/jrabbit/pyborg-1up.git#egg=pyborg\&subdirectory=pyborg`


Note that we're using Python 3.6+ (for fancy type declarations) and 2.7 (for now)


Basic Usage
-----------

`pyborg` is our new unified pyborg command line interface.


Documentation
-------------

[Docs can be found on RTD.](http://pyborg.readthedocs.io/en/latest/)


Notes
-----

Pyborg is skipping version 1.3; this was used for a transitory database/"brain" restructuring that was underwhelming. 

Ancient original tarballs may be found at http://download.gna.org/pyborg/

Pyborg was originally developed by Tom Morton and Sébastien Dailly.


Suggested NLTK data
-------------------

Pyborg can use nltk tagging and tokenizing when installed and configured. Tagging requires `averaged_perceptron_tagger` and tokenization requires `punkt`.


Todo:
-----

* spelling or better heuristics
* graphing and visualization of the database