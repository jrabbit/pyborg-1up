.. pyborg-1up documentation master file, created by
   sphinx-quickstart on Sun Jul  3 03:20:41 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

The pyborg documentation
======================================

Contents:

.. toctree::
   :maxdepth: 2
   
   command
   api
   deploy
   enduser
   changes



Pyborg is a `markov chain <https://en.wikipedia.org/wiki/Markov_chain>`_ bot for `IRC <https://en.wikipedia.org/wiki/Internet_Relay_Chat>`_ (and other services [even at the same time with the same database]) that generates replies based on messages and it's database.
Pyborg exists as a range of scripts, libraries and servers. 




Installing
==========

We're on the cheeseshop.

	pip install pyborg


optional extras:
   - nlp (need nltk data deps)
   - subtitles
   - systemd (for notify support in the http server app)

Advanced NLTK integration
-------------------------

 * install the nltk package
 * run `their downloader <http://www.nltk.org/data.html>`_ and select the the following packages:

 	* averaged_perceptron_tagger
	* punkt




Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

