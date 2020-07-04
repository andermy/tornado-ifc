from .base import BaseHandler
from marshmallow import ValidationError
#from persistence.schemas.user import UserSchema
from .error_throw import ErrorThrow
from logzero import logger
from http import HTTPStatus
from pymongo import *
import json

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
                print(result)
            else:
                result = self.collection.find_one(document_id=key)
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
