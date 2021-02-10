#from .base import BaseHandler
from marshmallow import ValidationError
#from persistence.schemas.user import UserSchema
#from .error_throw import ErrorThrow
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
from models import models

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
            return json.loads(self.request.body.decode('utf-8'))

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
            branch = self.get_argument('branch', 'master')
            version = self.get_argument('version', None)
            q = {'project': ObjectId(project), 'branch': branch}
            if version is not None:
                q['version'] = version
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
        #Only for creating new branch-version
        try:
            new_version = self.data_received()
            new_version['version'] = 0
            new_version['project'] = ObjectId(project)
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

class SiteHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('IfcStorey')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = self.collection.query(q)
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no product found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class BuildingHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('IfcBuilding')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = self.collection.query(q)
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no product found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class StoreyHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('IfcStorey')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = self.collection.query(q)
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no product found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class ProductHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('IfcProduct')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            storey = self.get_argument('storey', None)
            q = {"version": ObjectId(version)}
            if storey is not None:
                q['storey'] = int(storey)
            result = self.collection.query(q)
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no product found with id {}'.format(project))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class CalculationHandler(BaseHandler):
    mongoClient = None
    collection = None

    def prepare(self):
        self.settings['mongo'].define_collection('calculation')
        self.collection = self.settings['mongo']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body.decode('utf-8'))

    def get(self, key):
        try:
            if not key:
                result = self.collection.find_all()
            else:
                result = self.collection.find_one(document_id=str(key))
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no calculation found with id {}'.format(key))
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        
        self.write_response(status_code=HTTPStatus.OK,
                                result=result)

    def post(self, key):
        try:
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
                                 reason='no calculation found with id {}'.format(key))
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
            df = m.DataFrame.objects.get({'_id': ObjectId(key)})
                    
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
                    version = m.VersionResolver(project=df.project, branch=df.branch)
                    table = m.Table(version.get_latest_version())
                    table.create_from_ifc_products()
                    result = table.to_react_table_json()
                    self.write_response(status_code=HTTPStatus.OK,
                                            result=result)
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
            vr = m.Version.objects.get({'_id': ObjectId(version)})
            from_model = self.get_argument('from_model', None)
            print(from_model)
        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = m.DataFrame(from_model=from_model, name=new_DataFrame['name'], version=vr).save()
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=json.loads(json_util.dumps(response.to_son().to_dict())))

    def put(self, key):
        try:
            response = self.collection.update_one(document_id=key,
                                                        document=self.data_received())
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                                 reason='no calculation found with id {}'.format(key))
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
                             reason='no calculation found with id {}'.format(key))
        except Exception as ex:
            logger.error(ex)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(ex))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                message='the calculation was successfully deleted')