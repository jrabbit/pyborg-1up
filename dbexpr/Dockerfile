FROM python:3.8
COPY . /srv
RUN pip install sqlalchemy psycopg2-binary
ENTRYPOINT python /srv/db_tester.py
