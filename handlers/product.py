from marshmallow import ValidationError
from logzero import logger
from http import HTTPStatus
import json
import tornado.web
import uuid
import logging
import os
from bson.objectid import ObjectId
from bson import json_util

from handlers import BaseHandler, ErrorThrow
import models as m
import version_resolver as v

class ProductTypeHandler(BaseHandler):
    
    def prepare(self):
        #self.users_cache = self.settings['redis']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body.decode('utf-8'))

    def get(self, key):
        try:
            if not key:
                result = m.ProductType.objects.all()
                response = result.values()
            else:
                result = m.ProductType.objects.get({'_id': ObjectId(key)})
                response = json.loads(json_util.dumps(result.to_son().to_dict()))
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no productType found with id {}'.format(key))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=response)

    def post(self, key):
        try:
            #new_project = UserSchema().load(self.data_received())
            new_element = self.data_received()

        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = m.ProductType(name=new_element['name'], productType=new_element['producer']).save()
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result= json.loads(json_util.dumps(response.to_son().to_dict())))

    def put(self, key):
        try:
            new_element = self.data_received()
            old_element = m.ProductType.objects.get({'_id': ObjectId(key)})
            old_element.name = new_element['name']
            old_element.producer = new_element['producer']
            old_element.save()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no productType found with id {}'.format(key))
        except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=json.loads(json_util.dumps(old_element.to_son().to_dict())))

    def delete(self, key):
        try:
            m.ProductType.objects.get({'_id': ObjectId(key)}).delete()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no productType found with id {}'.format(key))
        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                message='the productType was successfully deleted')


routes = [
    (r"/api/v1/producttype/?(.*)?", ProductTypeHandler)
]