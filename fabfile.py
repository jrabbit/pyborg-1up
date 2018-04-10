from fabric.api import run, local, cd,env, lcd
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
        for unit in ["pyborg_discord.service", "pyborg_http.service"]:
            run("systemctl restart {}".format(unit))


def release():
    with lcd("pyborg"):
        local("rm -rf build") # clean build
        local("python --version")
        local("python setup.py bdist_wheel sdist")
        print("run `gpg -ba` on the files and upload with `twine`")

def lint():
    pass