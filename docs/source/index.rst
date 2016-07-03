.. pyborg-1up documentation master file, created by
   sphinx-quickstart on Sun Jul  3 03:20:41 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to pyborg-1up's documentation!
======================================

Contents:

.. toctree::
   :maxdepth: 2


Pyborg is a `markov chain <https://en.wikipedia.org/wiki/Markov_chain>`_ bot for `IRC <https://en.wikipedia.org/wiki/Internet_Relay_Chat>`_ (and other services) that generates replies based on messages and it's database.
Pyborg exists as a range of scripts, libraries and servers. 

Scripts
=======

pyborg_irc2.py
--------------
.. attention::
   ``pyborg_irc2.py`` requires a configure file, default name: ``example.irc.toml``
The rewritten irc module for pyborg. 
Usage: pyborg_irc2.py <start_irc_bot> [<verbose>] [<debug>] [<conffile>]


Command line options:

 *  :option:`-v` :option:`--verbose` -- set logging level to INFO
 *  :option:`-d` :option:`--debug`  -- set logging level to DEBUG
 *  :option:`-f` :option:`--conffile` specify a different conf file (default: ``example.irc.toml``)

pyborg_tumblr.py
----------------
.. attention::
   ``pyborg_tumblr.py`` requires a configure file default name: ``example.tumblr.toml``

Usage: pyborg_tumblr.py <start_tumblr_bot> [<verbose>] [<toml_conf>]


Command line options:

 *  :option:`--verbose` -- set logging level to INFO (default)
 *  :option:`-f` :option:`--toml_conf` -- 

pyborg-linein.py
----------------
PyBorg offline line input module.

Usage: pyborg-linein.py <start> [<multiplex>]


Options:

 *  :option:`-m` :option:`--multiplex` -- turns on multiplexing.


pyborg_http.py
--------------
The http server that allows "multiplexing", letting different pyborg clients share one database. This is a small server configured just for a few clients.

pyborg_http.py has no options currently.



The core of pyborg is contained in the :py:mod:`pyborg.pyborg` module.


.. autoclass:: pyborg.pyborg.pyborg
    :members: learn, unlearn, reply, replace
    :undoc-members:




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

