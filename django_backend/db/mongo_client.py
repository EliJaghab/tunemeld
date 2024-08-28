from pymongo import MongoClient
from django.conf import settings

class MongoDBClient:
    def __init__(self):
        self.client = MongoClient(settings.MONGO_URI)
        self.db = self.client[settings.MONGO_DB_NAME]

    def get_collection(self, collection_name):
        return self.db[collection_name]

    def read_data(self, collection_name, query=None):
        collection = self.get_collection(collection_name)
        return list(collection.find(query or {}))

    def read_one(self, collection_name, query):
        collection = self.get_collection(collection_name)
        return collection.find_one(query)
