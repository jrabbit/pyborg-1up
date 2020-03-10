FROM python:3.8
COPY . /srv
RUN pip install aiopg[sa]
ENTRYPOINT python /srv/db_tester.py
