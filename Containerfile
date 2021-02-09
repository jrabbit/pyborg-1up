FROM python:3.9

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY pyproject.toml poetry.lock /usr/src/app/

WORKDIR /usr/src/app

COPY . /usr/src/app

RUN pip install poetry && poetry install -v -E subtitles
EXPOSE 2001

CMD ["poetry", "run", "green"]
