from logzero import logger
from pymongo import MongoClient
from bson.json_util import dumps
from bson.objectid import ObjectId

import settings
import json

_mongo_client = None


class MongoDb():
    database_collection= None

    def __init__(self):
        self.get_mongo_client()

    def get_mongo_client(self):
        global _mongo_client
        try:
            _mongo_client = MongoClient(settings.MONGO_URI)[settings.MONGO_DB]
        except Exception as err:
            logger.error(err)
            _mongo_client = None
        return _mongo_client

    def define_collection(self, collection):
        self.database_collection = _mongo_client.get_collection(name=collection)

    def insert_one(self, data: dict):
        try:
            response = self.database_collection.insert_one(data)

        except Exception as ex:
            raise ex
        else:
            return str(response.inserted_id)
    
    def insert_many(self, data: list):
        try:
            response = self.database_collection.insert_many(data)

        except Exception as ex:
            raise ex
        else:
            return str(response)

    def find_all(self):
        try:
            response = self.database_collection.find()
        except Exception as ex:
            raise ex
        else:
            return list(json.loads(dumps(response)))
    
    def query(self, q):
        try:
            response = self.database_collection.find(q)
        except Exception as ex:
            raise ex
        else:
            return list(json.loads(dumps(response)))

    def find_one(self, document_id: str):
        try:
            response = self.database_collection.find_one({'_id': ObjectId(document_id)})
        except Exception as ex:
            raise ex
        else:
            if response is not None:
                return dict(json.loads(dumps(response)))
            else:
                raise ValueError

    def update_one(self, document_id, document):
        try:
            response = self.database_collection.find_one_and_update(
                {'_id': ObjectId(document_id)},
                {'$set': document},
                return_document=True)
        except Exception as ex:
            raise ex
        else:
            if response is None:
                raise ValueError
            else:
                return dict(json.loads(dumps(response)))

    def delete_one(self, document_id):
        try:
            response = self.database_collection.find_one_and_delete({'_id': ObjectId(document_id)})
        except Exception as ex:
            raise ex
        else:
            if response is None:
                raise ValueError
            else:
                pass