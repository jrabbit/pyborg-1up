Pyborg is a markov chain bot for irc that generates replies based on messages and it's database.

It was originally developed by Tom Morton and Sébastien Dailly.

Tarballs may be found at http://download.gna.org/pyborg/
Uses the pure python irc library "irclib" http://python-irclib.sourceforge.net/ (Known to to work with 1.30)

Done:
	* Python 2.6 Compat (One line with a lambada at the end of pyborg.py breaks here... I'll need some #python help on this one) *DONE*.
	* Python 3.0 Compat? *Works in 2.7, will keep it working on 2.7 as it will move toward 3.x*
Todo:
	* spelling or better heuristics
	* graphing and visualization of the database
	* Move to irclib? (mutli server capable, or make pyborg thread-able.)