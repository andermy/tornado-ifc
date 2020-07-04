# __init__.py
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.options import define, options
from tornado.web import Application
from .handlers import Project
import motorengine

define('port', default=8888, help='port to listen on')

def main():
    """Construct and serve the tornado application."""
    application = Application([
        (r"/projects", Project),
    ],debug=True)

    io_loop = IOLoop.instance()
    motorengine.connect("test", host="localhost", port=27017, io_loop=io_loop)
    
    http_server = HTTPServer(application)
    http_server.listen(options.port)
    print('Listening on http://localhost:%i' % options.port)
    IOLoop.current().start()
