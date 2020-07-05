from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from logzero import logger

from handlers.project import ProjectHandler
from handlers.uploadhandler import UploadHandler
import mongo

import settings

define('version', default=1)


def make_app():
    endpoints = [
        (r'/api/v1/projects/?(.*)?', ProjectHandler),
        (r'/api/v1/upload/?', UploadHandler,
             dict(upload_path="C:/UserData/z003rvhr/python/tornado_bim/tornado-bim/tmp", naming_strategy=None))
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