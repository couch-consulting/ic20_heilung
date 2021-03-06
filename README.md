# Strohristik Heilung IC2020

Beitrag zum [informatiCup 2020](https://github.com/informatiCup/informatiCup2020).
Implementierung einer Heuristik, die versucht in einem Spiel ausbrechende Pathogene so effektiv wie möglich zu bekämpfen.

## Setup

Es bestehen zwei verschiedene Möglichkeiten zum Setup.
Entweder lokal durch die Verwendung von Pipenv oder mit Hilfe von Docker.

### Pipenv

Für eine lokale Installation sind Python (>=3.6) und [Pipenv](https://pipenv.kennethreitz.org/en/latest/) erforderlich.

Anschließend sind für eine Installation und Start des Servers folgende Befehle auszuführen.

```bash
pipenv install
pipenv run python wsgi.py
```

Der Server ist nun lokal auf Port `50123` erreichbar.
Eine Änderung des Ports ist durch Anpassung in der [wsgi.py](wsgi.py) möglich.

### Docker

Dieses Repository enthält ein Dockerfile, welches mit Docker oder buildah gebaut werden kann.

```bash
buildah build-using-dockerfile -t ic20 .
```

Das dadurch generierte Image ist so konfiguriert standardmäßig Port 50123 weiterzuleiten.
Auf diesen ist auch die Anwendung konfiguriert.
Eine Container Runtime (z.B. docker oder podman) muss daher mit den Parametern `-P` oder `-p <local-port>:50123` werden.

```bash
sudo podman run -dt -p 50123:50123 couchconsulting/ic20
```

Ein bereits gebautes Image ist auf DockerHub als [`couchconsulting/ic20`](https://hub.docker.com/repository/docker/couchconsulting/ic20) verfügbar.

## Dokumentation

Für Klassen und Methoden existiert eine [separate Dokumentation](docs/html/index.html).
