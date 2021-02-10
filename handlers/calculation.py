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
from models import Calculation, DataFrame, Version
import version_resolver as v
import spreadsheet_flow as s

class CalculationHandler(BaseHandler):
    
    def prepare(self):
        #self.users_cache = self.settings['redis']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body.decode('utf-8'))

    def get(self, key):
        try:
            if key:
                result = Calculation.objects.get({'_id': ObjectId(key)})
                response = json.loads(json_util.dumps(result.to_son().to_dict()))
            else:
                dataframe = self.get_argument('dataframe', None)
                result = Calculation.objects.raw({'dataframe': ObjectId(dataframe)})
                response = result.values()

        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no calculation found with id {}'.format(key))
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
                response = Calculation(name=new_element['variable'], buildingType=new_element['recipe']).save()
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
            old_element = Calculation.objects.get({'_id': ObjectId(key)})
            old_element.name = new_element['variable']
            old_element.area = new_element['recipe']
            old_element.save()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no project found with id {}'.format(key))
        except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=json.loads(json_util.dumps(old_element.to_son().to_dict())))

    def delete(self, key):
        try:
            Calculation.objects.get({'_id': ObjectId(key)}).delete()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no calculation found with id {}'.format(key))
        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                message='the calculation was successfully deleted')

class DataFrameHandler(BaseHandler):
    
    def prepare(self):
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body.decode('utf-8'))

    def get(self, key):
        try:
            df = DataFrame.objects.get({'_id': ObjectId(key)})
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no DataFrame found with id {}'.format(key))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        else:
            try:
                if df.from_model == True:
                    version = v.VersionResolver(versionObject=df.version)
                    table = s.Table(version.get_latest_version())
                    table.create_from_ifc_products()
                    result = table.to_react_table_json()
                    response = json.loads(json_util.dumps(result.values()))
                    self.write_response(status_code=HTTPStatus.OK,
                                            result=response)
                else:
                    table = s.Table()
            except ValueError:
                raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                reason='no DataFrame found with id {}'.format(key))
            except Exception as err:
                logger.error(err)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                reason=str(err))


    def post(self, version):
        try:
            new_DataFrame = self.data_received()
            vr = Version.objects.get({'_id': ObjectId(version)})
            from_model = self.get_argument('from_model', None)
        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = DataFrame(from_model=from_model, name=new_DataFrame['name'], version=vr).save()
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=json.loads(json_util.dumps(response.to_son().to_dict())))

    def put(self, key):
        try:
            new_element = self.data_received()
            old_element = DataFrame.objects.get({'_id': ObjectId(key)})
            old_element.from_model = new_element['from_model']
            old_element.name = new_element['name']
            old_element.save()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no Dataframe found with id {}'.format(key))
        except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=json.loads(json_util.dumps(old_element.to_son().to_dict())))

    def delete(self, key):
        try:
            DataFrame.objects.get({'_id': ObjectId(key)}).delete()
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no calculation found with id {}'.format(key))
        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                message='the Dataframe was successfully deleted')

routes = [
    (r'/api/v1/calculation/?(.*)?', CalculationHandler),
    (r'/api/v1/dataframe/?(.*)?', DataFrameHandler)
]