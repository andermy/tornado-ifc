from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from logzero import logger

from handlers.projecthandler import ProjectHandler, VersionHandler, ProjectProductHandler
from handlers.ifcfilehandler import IfcFileHandler
import mongo

import settings

define('version', default=1)


def make_app():
    endpoints = [
        (r'/api/v1/projects/?(.*)?', ProjectHandler),
        (r'/api/v1/version/?(.*)?', VersionHandler),
        (r'/api/v1/product/?(.*)?', ProjectProductHandler),
        (r'/api/v1/upload/?', IfcFileHandler,
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