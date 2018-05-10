from fabric.api import cd, env, lcd, local, run, settings

env.use_ssh_config = True
env.hosts = ["trotsky"]


def bandit():
    local("/home/jack/.virtualenvs/bandit/bin/bandit -r pyborg")


def deploy():
    local("git push --all")
    with cd("src/pyborg-1up"):
        run("git stash")
        # verfiy tag here?
        run("git pull")
        run("git stash pop")
        # restart units
        for unit in ["pyborg_discord.service", "pyborg_http.service", "pyborg_twitter.service"]:
            run("systemctl restart {}".format(unit))


def release():
    "make a release of pyborg"
    with lcd("pyborg"):
        local("rm -rf build")  # clean build
        local("python --version")
        local("python setup.py bdist_wheel sdist")
        print("run `gpg -ba` on the files and upload with `twine`")


def outdated():
    local("pipenv run pip list -o --format=columns")


def lint():
    "run mypy etc"
    with settings(warn_only=True):
        local("pipenv run mypy pyborg/pyborg")
        local('flake8 --count')
