Making a pyborg module: a step by step case-study
=================================================

Audience: Python developers of all stripes.

This guide assumes you have a functioning `install of pyborg and it's dev-deps. <https://github.com/jrabbit/pyborg-1up/blob/master/CONTRIBUTING.md#development-workflow>`_

.. sectnum::

Picking your battle
-------------------

A good service to port pyborg to will have a simple API, a token auth scheme, and strong python libraries.

So we're going to pick a bad example potentially so it's fair. Keybase chat has been an idea for a while here now.

The end goal will be to have a pyborg subcommand that connects to our configured keybase chat room that can reply and learn.


Preperation
-----------

- Make module file in the right place. `pyborg/pyborg/mod/mod_keybase.py`
- (optionally) Make a git branch


Sketch out the class
--------------------


Add it to the entrypoint
------------------------

- add the imports to the top of `pyborg/pyborg_entrypoint.py` keeping in mind any python incompatibilities.
- write a function that calls your bot and wrap it with the decorators needed.
- Use try/except clauses for cleanup/KeyInterrupt behavior::

  @cli_base.command()
  @click.option("--multiplex", default=True, type=click.BOOL)
  @click.option("--conf-file", default=os.path.join(folder, "keybase.toml"))
  def keybase(conf_file, multiplex):
        try:
            mod = PyborgKeybase()
            mod.start()
        except Exception:
            mod.teardown()
            raise

