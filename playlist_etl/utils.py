import os
from datetime import datetime, timezone

from dotenv import load_dotenv
from pymongo import MongoClient

PLAYLIST_ETL_COLLECTION_NAME = "playlist_etl"


def set_secrets():
    if not os.getenv("GITHUB_ACTIONS"):
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        print("env_path" + env_path)
        load_dotenv(dotenv_path=env_path)


def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI environment variable not set")
    return MongoClient(mongo_uri)


def insert_data_to_mongo(client, collection_name, document):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    document["insert_timestamp"] = datetime.now(timezone.utc)
    result = collection.insert_one(document)
    print(f"Data inserted with id: {result.inserted_id}")


def read_cache_from_mongo(mongo_client, collection_name):
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    cache = {}
    for item in collection.find():
        cache[item["key"]] = item["value"]
    return cache


def update_cache_in_mongo(mongo_client, collection_name, key, value):
    print(f"Updating cache in collection: {collection_name} for key: {key} with value: {value}")
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    collection.replace_one({"key": key}, {"key": key, "value": value}, upsert=True)


def read_data_from_mongo(client, collection_name):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    return list(collection.find())


def clear_collection(client, collection_name):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    collection.delete_many({})
    print(f"Cleared collection: {collection_name}")
