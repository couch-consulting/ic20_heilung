FROM python:3.7-buster

RUN pip install pipenv
RUN groupadd -r heilung && useradd -r -s /bin/false -g heilung heilung

WORKDIR /usr/src/app
COPY --chown=heilung:heilung server.py wsgi.py Pipfile Pipfile.lock /usr/src/app/
COPY --chown=heilung:heilung heilung heilung/
RUN pipenv install --system
USER heilung

EXPOSE 50123
ENTRYPOINT python wsgi.py
