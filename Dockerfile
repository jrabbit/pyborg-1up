FROM python:2-alpine

LABEL maintainer "jackjrabbit@gmail.com"

RUN mkdir -p /usr/src/pyborg

COPY pyborg /usr/src/pyborg

RUN pip --no-cache-dir install -e /usr/src/pyborg

WORKDIR /usr/src/pyborg

CMD ["pyborg", "linein"]