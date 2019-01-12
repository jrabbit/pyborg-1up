from invoke import task
from fabric2 import Connection

@task
def deploy(c, restart=False):
    c.run("git push --all")
    conn = Connection("trotsky")
    with conn.cd("src/pyborg-1up"):
        conn.run("git fetch")
        conn.run("git stash")
        conn.run("git pull")
        conn.run("git stash pop")
        conn.run("~/.local/bin/pipenv sync") # they all use the same pipenv managed virtualenv
        if restart:
            for unit in ["pyborg_discord", "pyborg_http", "pyborg_twitter", "pyborg_mastodon"]:
                conn.sudo("systemctl restart {}".format(unit), pty=True)
        print("Deploy Completed.")

@task
def bandit(c):
    c.run("pipenv run bandit --exclude=build,test -s B311 -r pyborg", pty=True)