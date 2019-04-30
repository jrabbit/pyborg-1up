Making a pyborg module: a step by step case-study
=================================================

Audience: Python developers of all stripes.

This guide assumes you have a functioning `install of pyborg and it's dev-deps. <https://github.com/jrabbit/pyborg-1up/blob/master/CONTRIBUTING.md#development-workflow>`_


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
             mod = PyborgKeybase(conf_file)
             mod.start()
         except Exception:
             mod.teardown()
	     raise


Test your code
--------------

Invoking your code via the pyborg cli command will let you debug on a basic level, check the logging options for more output.

Run the tests included and potentially write new ones to cover any expanded pyborg functionality and the module.

Tests can be invoked by `green` (current python version only) or `tox` (all supported versions)

Linters are availible under an invoke function: `inv lint` will lint the entire project.


Commit your work
----------------

Use whatever git client. on the cli it'd be like `git add pyborg/ && git commit -m "my commit message"`

Push this to your fork. (You can add a remote after cloning if you didn't already fork pyborg.)


Create a Pull Request
---------------------

Please open a pull request if you add a module for a service other people would use! It should be GPLv3 licensed.

Travis tests will run against your code. There are no coverage requirements.
