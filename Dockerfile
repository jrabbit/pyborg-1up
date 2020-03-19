FROM python:3-slim

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY pyproject.toml poetry.lock /usr/src/app/

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install poetry && poetry install --no-dev -v -E subtitles -E nlp

EXPOSE 2001

CMD ["poetry", "run", "pyborg", "linein", "--multiplex", "false"]