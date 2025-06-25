import os
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient
from pymongo.collection import Collection

from playlist_etl.config import PLAYLIST_ETL_DATABASE, TRACK_COLLECTION
from playlist_etl.helpers import get_logger, set_secrets
from playlist_etl.models import Track

logger = get_logger(__name__)


class MongoDBClient:
    def __init__(self):
        set_secrets()
        mongo_uri = os.getenv("MONGO_URI")
        if not mongo_uri:
            raise Exception("MONGO_URI environment variable not set")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[PLAYLIST_ETL_DATABASE]
        self.track_collection = self.get_collection(TRACK_COLLECTION)

    def get_collection(self, collection_name: str) -> Collection[Any]:
        return self.db[collection_name]

    def insert_or_update_data(self, collection_name: str, document: dict[str, Any]) -> None:
        collection = self.get_collection(collection_name)
        if "_id" in document:
            existing_document = collection.find_one({"_id": document["_id"]})
            if existing_document:
                document["update_timestamp"] = datetime.now(timezone.utc)
                collection.replace_one({"_id": document["_id"]}, document)
                logger.info(f"Data updated for id: {document['_id']}")
                return
        document["insert_timestamp"] = datetime.now(timezone.utc)
        result = collection.insert_one(document)
        logger.info(f"Data inserted with id: {result.inserted_id}")

    def insert_or_update_kv_data(self, collection_name: str, key: str, value: Any) -> None:
        collection = self.get_collection(collection_name)
        existing_document = collection.find_one({"key": key})
        timestamp = datetime.now(timezone.utc)
        if existing_document:
            update_data = {"key": key, "value": value, "update_timestamp": timestamp}
            collection.replace_one({"key": key}, update_data)
            logger.info(f"KV data updated for key: {key}")
        else:
            insert_data = {"key": key, "value": value, "insert_timestamp": timestamp}
            collection.insert_one(insert_data)
            logger.info(f"KV data inserted with key: {key}")

    def read_cache(self, collection_name: str) -> dict[str, Any]:
        collection = self.get_collection(collection_name)
        cache = {}
        for item in collection.find():
            cache[item["key"]] = item["value"]
        return cache

    def update_cache(self, collection_name: str, key: str, value: Any) -> None:
        logger.info(f"Updating cache in collection: {collection_name} for key: {key}")
        collection = self.get_collection(collection_name)
        collection.replace_one({"key": key}, {"key": key, "value": value}, upsert=True)

    def read_data(self, collection_name: str) -> list[dict[str, Any]]:
        collection = self.get_collection(collection_name)
        return list(collection.find())

    def clear_collection(self, collection_name: str) -> None:
        collection = self.get_collection(collection_name)
        collection.delete_many({})
        logger.info(f"Cleared collection: {collection_name}")

    def collection_is_empty(self, collection_name: str) -> bool:
        collection = self.get_collection(collection_name)
        return collection.count_documents({}) == 0

    def overwrite_collection(self, collection_name: str, documents: list[dict[str, Any]]) -> None:
        self.clear_collection(collection_name)
        collection = self.get_collection(collection_name)
        if documents:
            collection.insert_many(documents)
            logger.info(f"Overwritten collection: {collection_name} with {len(documents)} documents")

    def overwrite_kv_collection(self, collection_name: str, kv_dict: dict[str, Any]) -> None:
        self.clear_collection(collection_name)
        collection = self.get_collection(collection_name)
        documents = [{"key": key, "value": value} for key, value in kv_dict.items()]
        if documents:
            collection.insert_many(documents)
            logger.info(f"Overwritten KV collection: {collection_name} with {len(documents)} entries")

    def update_track(self, track: Track) -> None:
        self.track_collection.update_one({"isrc": track.isrc}, {"$set": track.model_dump()}, upsert=True)

    def get_collection_count(self, collection: Collection) -> int:
        return collection.count_documents({})
