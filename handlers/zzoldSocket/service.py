from motor.motor_tornado import MotorClient
from tornado import gen


class StoreClient(object):

    def __init__(self, user="test", password="test", database="project_data"):
        userAndPass = ""
        if user and password:
            userAndPass = user + ":" + str(password) + "@"
        url = "mongodb+srv://"+ userAndPass + "nibanfinance-lgkjt.gcp.mongodb.net/test?retryWrites=true&w=majority"
        self.collection = MotorClient(url).store_collection

    @gen.coroutine
    def get(self, key):
        result = yield self.collection.find_one({'key': key})
        return result['value'] if result else 'null'

    @gen.coroutine
    def set(self, key, value):
        result = yield self.collection.insert({'key': key, 'value': value})
        return 'ok'

