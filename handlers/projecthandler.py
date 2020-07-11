from .base import BaseHandler
from marshmallow import ValidationError
#from persistence.schemas.user import UserSchema
from .error_throw import ErrorThrow
from logzero import logger
from http import HTTPStatus
from pymongo import *
import json
import tornado.web
import uuid
import logging
import os

class ProjectHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('projects')
        self.collection = self.settings['mongo']
        #self.users_cache = self.settings['redis']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, key):
        try:
            if not key:
                result = self.collection.find_all()
            else:
                result = self.collection.find_one(document_id=str(key))
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no project found with id {}'.format(key))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=result)

    def post(self, key):
        try:
            #new_project = UserSchema().load(self.data_received())
            new_project = self.data_received()

        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = self.collection.insert_one(data=new_project)
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                new_project = self.collection.find_one(document_id=response)
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=new_project)

    def put(self, key):
        try:
            response = self.collection.update_one(document_id=key,
                                                        document=self.data_received())
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no project found with id {}'.format(key))
        except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=response)

    def delete(self, key):
        try:
            self.collection.delete_one(document_id=key)
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no project found with id {}'.format(key))
        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                message='the project was successfully deleted')

class VersionHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.mongoClient = self.settings['mongo'].get_mongo_client()
        self.settings['mongo'].define_collection('version')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

    def get(self, project):
        try:
            version = self.get_argument('version', 'master')
            if not project:
                result = self.collection.find_all()
            else:
                q = {'project': project, 'version': version}
                result = self.collection.query(q)
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no project found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=result)


    def post(self, project):
        try:
            new_version = self.data_received()
            new_version['project'] = project
        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = self.collection.insert_one(data=new_version)
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                new_version = self.collection.find_one(document_id=response)
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=new_version)

    def put(self, key):
        try:
            response = self.collection.update_one(document_id=key,
                                                        document=self.data_received())
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no version found with id {}'.format(key))
        except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=response)

class ProjectProductHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('product')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, project):
        try:
            version = self.get_argument('version', 'master')
            if not project:
                result = self.collection.find_all()
            else:
                q = {'project': project, 'version': version}
                result = self.collection.query(q)
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no project found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=result)