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

class ProjectHandler(BaseHandler):
    
    def prepare(self):
        #self.users_cache = self.settings['redis']
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body.decode('utf-8'))

    def get(self, key):
        try:
            if not key:
                result = m.Project.objects.all()
                response = result.values()
            else:
                result = m.Project.objects.get({'_id': ObjectId(key)})
                response = json.loads(json_util.dumps(result.to_son().to_dict()))
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no project found with id {}'.format(key))
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
                response = m.Project(name=new_element['name'], buildingType=new_element['building_type'], area=new_element['area']).save()
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
            old_element = m.Project.objects.get({'_id': ObjectId(key)})
            old_element.name = new_element['name']
            old_element.area = new_element['area']
            old_element.buildingType = new_element['building_type']
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
            m.Project.objects.get({'_id': ObjectId(key)}).delete()
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

    def prepare(self):
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
            result = m.Version.objects.raw({q}).values()
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
            branch = self.get_argument('branch', 'master')
            vs = v.VersionResolver(project=project, branch=branch)
            new_version = vs.create_new_version()
        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                response = json.loads(json_util.dumps(new_version.to_son().to_dict()))
            except Exception as ex:
                logger.error(ex)
                raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                                 reason=str(ex))
            else:
                self.write_response(status_code=HTTPStatus.CREATED,
                                    result=response)

class SiteHandler(BaseHandler):

    def prepare(self):
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = m.IfcSite.objects.raw({q})
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no IfcSite found')
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result.values())

class BuildingHandler(BaseHandler):

    def prepare(self):
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = m.IfcBuilding.objects.raw({q})
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no Building found')
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result.values())

class StoreyHandler(BaseHandler):

    def prepare(self):
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = m.IfcStorey.objects.raw({q})
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no Storey found')
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class SpaceHandler(BaseHandler):

    def prepare(self):
        pass

    def data_received(self, chunk=None):
        if self.request.body:
            return json.loads(self.request.body)

   
    def get(self, version):
        try:
            q = {"version": ObjectId(version)}
            result = m.IfcSpace.objects.raw({q})
            
        except ValueError:
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason='no Storey found')
        except Exception as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
                             reason=str(err))
        else:
            self.write_response(status_code=HTTPStatus.OK,
                                result=result)

class ProductHandler(BaseHandler):

    def prepare(self):
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
            result = m.IfcProduct.objects.raw({q})
            
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

    def post(self, productType):
        try:
            #new_project = UserSchema().load(self.data_received())
            new_element = self.data_received()
            space = self.get_argument('space', None)
            system = self.get_argument('system', None)
        except ValidationError as err:
            logger.error(err)
            raise ErrorThrow(status_code=HTTPStatus.BAD_REQUEST,
                             reason=str(err))
        else:
            try:
                productType = m.ProductType.objects.get({'_id': ObjectId(productType)})
                if space is not None:
                    space = m.IfcSpace.objects.get({'_id': ObjectId(space)})
                if system is not None:
                    system = m.IfcSystem.objects.get({'_id': ObjectId(system)})
                response = m.IfcProduct(name=new_element['name'], buildingType=new_element['building_type'], area=new_element['area']).save()
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
            old_element = m.Project.objects.get({'_id': ObjectId(key)})
            old_element.name = new_element['name']
            old_element.area = new_element['area']
            old_element.buildingType = new_element['building_type']
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
            m.Project.objects.get({'_id': ObjectId(key)}).delete()
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

routes = [
    (r"/api/v1/project/?(.*)?", ProjectHandler),
    (r'/api/v1/version/?(.*)?', VersionHandler),
    (r'/api/v1/ifcsite/?(.*)?', SiteHandler),
    (r'/api/v1/ifcbuilding/?(.*)?', BuildingHandler),
    (r'/api/v1/ifcstorey/?(.*)?', StoreyHandler),
    (r'/api/v1/ifcspace/?(.*)?', SpaceHandler),
    (r'/api/v1/ifcproduct/?(.*)?', ProductHandler)
]