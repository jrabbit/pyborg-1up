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
def docs(c):
    "run autobuilder for local docs generation"
    c.run("pipenv run sphinx-autobuild docs/source docs/build", pty=True)

@task
def test(c):
    "this runs tox, just use tox :)"
    c.run("tox")


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
