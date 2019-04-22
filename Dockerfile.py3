FROM python:3-slim

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY Pipfile Pipfile.lock /usr/src/

COPY pyborg /usr/src/pyborg

WORKDIR /usr/src/

RUN pip install pipenv && pipenv install

CMD ["pipenv", "run", "pyborg", "linein", "--multiplex", "false"]