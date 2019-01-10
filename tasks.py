from invoke import task

@task
def bandit(c):
    c.run("pipenv run bandit --exclude=build,test -s B311 -r pyborg", pty=True)