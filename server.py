from tornado.web import Application
from tornado.ioloop import IOLoop
from tornado.httpserver import HTTPServer
from tornado.options import define, options
from logzero import logger

#from projecthandler import ProjectHandler, VersionHandler, ProductHandler, DataFrameHandler
#from ifcfilehandler import IfcFileHandler
#import mongo
from pymodm.connection import connect
import settings as s
from handlers import project, ifcfile, calculation, product


define('version', default=1)


def make_app():

    routes = []
    routes.extend(project.routes)
    routes.extend(ifcfile.routes)
    routes.extend(calculation.routes)
    routes.extend(product.routes)
    
    #endpoints = [
    #    (r'/api/v1/projects/?(.*)?', h.ProjectHandler),
    #    (r'/api/v1/version/?(.*)?', h.VersionHandler),
    #    (r'/api/v1/product/?(.*)?', h.ProductHandler),
    #    (r'/api/v1/dataframe/?(.*)?', h.DataFrameHandler),
    #    (r'/api/v1/upload/?', h.IfcFileHandler,
    #         dict(upload_path="C:/UserData/z003rvhr/python/tornado_bim/tornado-bim/tmp", naming_strategy=None))
    #]

    return Application(routes,
                       debug=True,
                       mongo=connect(s.MONGO_URI, alias="my-app"))


if __name__ == '__main__':
    app = make_app()
    s.config_logs()
    http_server = HTTPServer(app)
    http_server.listen(8888)
    logger.info('Listening server on port 8888')
    IOLoop.current().start()