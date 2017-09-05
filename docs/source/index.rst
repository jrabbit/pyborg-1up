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



.. click:: pyborg_experimental:cli_base
   :prog: pyborg
   :show-nested:



API
===

The core of pyborg is contained in the :py:mod:`pyborg.pyborg` module.


.. autoclass:: pyborg.pyborg.pyborg
    :members: learn, unlearn, reply, replace
    :undoc-members:




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

