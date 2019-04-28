from pprint import pprint

import attr
from invoke import task
from fabric2 import Connection


@task
def deploy(c, restart=False, sync=False):
    "push code to a server (configure your own here)"

    c.run("git push --all")
    conn = Connection("trotsky")
    with conn.cd("src/pyborg-1up"):
        conn.run("git fetch")
        conn.run("git stash")
        conn.run("git pull")
        conn.run("git stash pop")
        if sync:
            conn.run("~/.local/bin/pipenv sync")  # they all use the same pipenv managed virtualenv
        if restart:
            for unit in ["pyborg_discord", "pyborg_http", "pyborg_twitter", "pyborg_mastodon"]:
                conn.sudo("systemctl restart {}".format(unit), pty=True)
        print("Deploy Completed.")


@task
def release(c, clean=True, docker=False):
    "cut a release of pyborg"

    with c.cd("pyborg"):
        if clean:
            c.run("pipenv run python setup.py clean")
            c.run("rm -rf build pyborg.egg-info")
        c.run("pipenv run python --version", echo=True)
        c.run("pipenv run python setup.py bdist_wheel sdist")
        print("now run `gpg -ba` on the files in pyborg/dist/ and upload with `twine`")
    if docker:
        # Build and push jrabbit/pyborg[:3], needs working d-c and docker
        c.run("docker-compose build")
        c.run("docker-compose push")


@task
def bandit(c):
    "security audit tool"
    c.run("pipenv run bandit --exclude=build,test -s B311 -r pyborg", pty=True)

@task
def docs(c, lan=False):
    "run autobuilder for local docs generation"
    if lan:
        opt = "-H 0.0.0.0 -p 3030"
    else:
        opt = ""
    c.run("pipenv run sphinx-autobuild docs/source docs/build {}".format(opt), pty=True)

@task
def test(c):
    "this runs tox, just use tox :)"
    c.run("tox")


@task
def docker_gauntlet(c):
    "there's so many ways to fuck this up on install let's try them all!"
    versions_list = ["2", "3.6", "3.7", "3"]
    for py_version in versions_list:
        c.run("docker pull python:{}".format(py_version))
    @attr.s
    class Strat():
        name = attr.ib()
        cmd = attr.ib()
        wheel = attr.ib(default=None)
    import pyborg
    whl_version = pyborg.__version__
    strats = [Strat(name="pip_wheel", cmd="pip install /srv/src/pyborg_1up/pyborg/dist/{wheel} && pyborg version", wheel="pyborg-{}-py2.py3-none-any.whl".format(whl_version)),
              Strat(name="pip_install_src", cmd="pip install /srv/src/pyborg1_up/pyborg && pyborg version"),
              Strat(name="pipenv", cmd="pip install pipenv && cd /srv/src/pyborg1_up/ && pipenv sync && pipenv run pyborg version")
             ]
    results = {}
    for py_version in versions_list:
        # docker scripting to install via pip, pipenv and setuptools (the first two work normally, but test build arefacts)
        for strat in strats:
            print(py_version, strat.name)
            if strat.wheel:
                lcmd = strat.cmd.format(wheel=strat.wheel)
            else:
                lcmd = strat.cmd
            ret = c.run("docker run -v $PWD:/srv/src/pyborg1_up -v $PWD/misc/docker_caches:/root/.cache --rm -it python:{} bash -c '{cmd}'".format(py_version, cmd=lcmd), pty=True, warn=True)
            results["{}_{}".format(py_version, strat.name)] = ret.ok
    pprint(results)

@task
def outdated(c):
    "outdated packages"
    c.run("pipenv run pip list -o --format=columns")


@task
def lint(c, mypy=True):
    "style & type checks"
    if mypy:
        c.run("pipenv run mypy pyborg/pyborg", warn=True)
    c.run("flake8 --config=tox.ini --count pyborg", warn=True)
