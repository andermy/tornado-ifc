from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from logzero import logger

from handlers.project import ProjectHandler
import mongo

import settings

define('version', default=1)


def make_app():
    endpoints = [
        (r'/api/v1/projects/?(.*)?'.format(options.version), ProjectHandler)
    ]

    return Application(endpoints,
                       debug=True,
                       mongo=mongo.MongoDb())


if __name__ == '__main__':
    app = make_app()
    settings.config_logs()
    http_server = HTTPServer(app)
    http_server.listen(8888)
    logger.info('Listening server on port 8888')
    IOLoop.current().start()