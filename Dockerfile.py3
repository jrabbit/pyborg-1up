FROM python:3-alpine

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY pyborg /usr/src/pyborg

RUN pip --no-cache-dir install -e /usr/src/pyborg && pip --no-cache-dir install discord.py

WORKDIR /usr/src/pyborg

CMD ["pyborg", "linein"]