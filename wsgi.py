from cheroot.wsgi import PathInfoDispatcher
from cheroot.wsgi import Server as WSGIServer

from server import app

app.config['NO_OBS'] = True
app.config['SILENT'] = False

d = PathInfoDispatcher({'/': app})
server = WSGIServer(('0.0.0.0', 8080), d)

if __name__ == '__main__':
    try:
        server.start()
    except KeyboardInterrupt:
        server.stop()
