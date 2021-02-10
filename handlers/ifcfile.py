# Handles file uploads in Python Tornado: http://tornadoweb.org/

import tornado.web
import tornado.iostream
import logging
import os
import uuid
import json
from .error_throw import ErrorThrow
from logzero import logger
from http import HTTPStatus
from .base import BaseHandler 
from tornado import gen
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor

import datetime
#from ifcFlow5 import IfcFile
from bson.objectid import ObjectId
from bson.json_util import dumps

from handlers import BaseHandler, ErrorThrow
import models as m
import version_resolver as v


MAX_WORKERS = 16

class IfcFileHandler(BaseHandler):
    "Handle file uploads."
    executor = ThreadPoolExecutor(max_workers=MAX_WORKERS)
    mongoClient = None
    collection = None

    def prepare(self):
        pass

    def initialize(self, upload_path, naming_strategy):
        """Initialize with given upload path and naming strategy.
        :keyword upload_path: The upload path.
        :type upload_path: str
        """
        self.upload_path = upload_path

    @tornado.gen.coroutine
    def post(self):
        fileinfo = self.request.files['filearg'][0]
        filename = fileinfo['filename']
        
        version = self.get_body_argument("version", default=None, strip=False)
        vr = v.VersionResolver(version)
        new_version_object = vr.create_new_version()
        
        try:
            with open(os.path.join(self.upload_path, filename), 'wb') as fh:
                fh.write(fileinfo['body'])
                logging.info("%s uploaded %s, saved as %s",
                         str(self.request.remote_ip),
                         str(fileinfo['filename']),
                         filename)
        except IOError as e:
            logging.error("Failed to write file due to IOError %s", str(e))
        else:
            try:
                new_file = m.IfcFile(filename= filename, path= os.path.join(self.upload_path, filename), version= new_version_object, created= datetime.datetime.now(), project=new_version_object.project).save()
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                self.new_file = new_file
                res = yield self.background_task(new_file)
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=new_file.values())
                                      
                
    @run_on_executor
    def background_task(self, new_file):
        try:
            if self.new_file.filename.endswith('.ifc'):
                print("It's ifc")
                #ifcData = IfcFile(new_file)

        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                    reason=str(ex))
        #else:  
        
    def get(self, project):
        try:
            result = m.IfcFile.objects.raw({'project': ObjectId(project)}).values()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no file in project')
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=result.values())


class DownloadHandler(tornado.web.RequestHandler):
    async def get(self, filename):
        # chunk size to read
        chunk_size = 1024 * 1024 * 1 # 1 MiB

        with open(filename, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                try:
                    self.write(chunk) # write the chunk to response
                    await self.flush() # send the chunk to client
                except tornado.iostream.StreamClosedError:
                    # this means the client has closed the connection
                    # so break the loop
                    break
                finally:
                    # deleting the chunk is very important because 
                    # if many clients are downloading files at the 
                    # same time, the chunks in memory will keep 
                    # increasing and will eat up the RAM
                    del chunk


routes = [
    (r'/api/v1/fileupload/?(.*)?', IfcFileHandler),
    (r'/api/v1/download/?(.*)?', DownloadHandler)
]