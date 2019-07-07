FROM python:2-slim

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY pyproject.toml poetry.lock /usr/src/

COPY pyborg /usr/src/pyborg

WORKDIR /usr/src/

RUN pip install poetry && poetry install -v

CMD ["poetry", "run", "pyborg", "linein", "--multiplex", "false"]