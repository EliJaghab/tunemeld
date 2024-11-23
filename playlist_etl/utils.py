import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

import psutil
from fp.fp import FreeProxy
from pymongo import MongoClient
from pymongo.collection import Collection
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from webdriver_manager.chrome import ChromeDriverManager

from playlist_etl.config import SPOTIFY_ERROR_THRESHOLD, SPOTIFY_VIEW_COUNT_XPATH
from playlist_etl.helpers import get_logger
from playlist_etl.mongo_db_client import MongoDBClient

PLAYLIST_ETL_COLLECTION_NAME = "playlist_etl"

logger = get_logger(__name__)


def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI environment variable not set")
    return MongoClient(mongo_uri)


def get_mongo_collection(mongo_client: MongoClient, collection_name: str) -> Collection:
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    return db[collection_name]


def get_spotify_client() -> Spotify:
    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise ValueError("Spotify client ID or client secret not found.")

    spotify = Spotify(
        client_credentials_manager=SpotifyClientCredentials(
            client_id=client_id, client_secret=client_secret
        )
    )
    return spotify


def insert_or_update_data_to_mongo(client, collection_name, document):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    if "_id" in document:
        existing_document = collection.find_one({"_id": document["_id"]})

        if existing_document:
            document["update_timestamp"] = datetime.now(timezone.utc)
            result = collection.replace_one({"_id": document["_id"]}, document)
            logger.info(f"Data updated for id: {document['_id']}")
            return

    document["insert_timestamp"] = datetime.now(timezone.utc)
    result = collection.insert_one(document)
    logger.info(f"Data inserted with id: {result.inserted_id}")


def insert_or_update_kv_data_to_mongo(client, collection_name, key, value):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    existing_document = collection.find_one({"key": key})

    if existing_document:
        update_data = {"key": key, "value": value, "update_timestamp": datetime.now(timezone.utc)}
        result = collection.replace_one({"key": key}, update_data)
        logger.info(f"KV data updated for key: {key}")
    else:
        insert_data = {"key": key, "value": value, "insert_timestamp": datetime.now(timezone.utc)}
        result = collection.insert_one(insert_data)
        logger.info(f"KV data inserted with key: {key}")


def read_cache_from_mongo(mongo_client, collection_name):
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    cache = {}
    for item in collection.find():
        cache[item["key"]] = item["value"]
    return cache


def update_cache_in_mongo(mongo_client, collection_name, key, value):
    logger.info(
        f"Updating cache in collection: {collection_name} for key: {key} with value: {value}"
    )
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
    logger.info(f"Cleared collection: {collection_name}")


def collection_is_empty(collection_name, mongo_client) -> bool:
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    return not read_data_from_mongo(mongo_client, collection_name)


class WebDriverManager:
    def __init__(self, use_proxy=False, memory_threshold_percent=75):
        self.use_proxy = use_proxy
        self.memory_threshold_percent = memory_threshold_percent
        self.driver = None
        self.spotify_error_count = 0

    def find_element_by_xpath(
        self,
        url: str,
        xpath: str,
        attribute: str = None,
        retries: int = 5,
        retry_delay: int = 10,
    ) -> str:
        if not hasattr(self, "driver") or not self.driver:
            self.driver = self._create_webdriver(self.use_proxy)

        def _attempt_find_element() -> str:
            try:
                self.driver.implicitly_wait(8)
                logger.info(f"Navigating to URL: {url}")
                self.driver.get(url)

                max_timeout = 15
                start_time = time.time()

                while time.time() - start_time < max_timeout:
                    element = self.driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        if attribute:
                            element_value = element.get_attribute(attribute)
                            logger.info(f"Successfully found element attribute: {element_value}")
                            return element_value
                        else:
                            element_text = element.text
                            logger.info(f"Successfully found element text: {element_text}")
                            return element_text

                logging.warning("Element not found even after waiting")
                return "Element not found"

            except TimeoutException:
                logging.error("Timed out waiting for element")
                return "Timed out waiting for element"
            except NoSuchElementException:
                logging.error("Element not found on the page")
                return "Element not found on the page"
            except Exception as e:
                error_message = str(e)
                logging.error(f"An error occurred: {error_message}")

                if self._is_rate_limit_issue(error_message):
                    logger.info("Rate limit detected, switching proxy and retrying...")
                    self._restart_driver(new_proxy=True)
                    return "Rate limit detected, retrying with new proxy..."

                return f"An error occurred: {error_message}"

        logger.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")

        result = self._retry_with_backoff(retries, retry_delay, _attempt_find_element)

        # Check if rate limiting or other errors occurred, retry with proxy if needed
        if self._is_error_occurred(result):
            if "Rate limit detected" in result:
                logger.info("Retrying with a new proxy due to rate limit detection.")
            self._restart_driver(new_proxy=("Rate limit detected" in result))

            # Retry again after restarting the driver with the new proxy if rate limited
            result = self._retry_with_backoff(retries, retry_delay, _attempt_find_element)

        return result

    def _retry_with_backoff(self, retries: int, retry_delay: int, action):
        attempt = 1
        while attempt <= retries:
            result = action()

            if not self._is_error_occurred(result):
                return result

            logger.info(f"Retrying... (attempt {attempt + 1} of {retries})")
            time.sleep(retry_delay * (2 ** (attempt - 1)))  # Exponential backoff
            attempt += 1

        return result

    def _is_error_occurred(self, result: str) -> bool:
        error_conditions = [
            "An error occurred",
            "Timed out waiting for element",
            "Element not found on the page",
            "Element not found",
        ]
        return any(condition in result for condition in error_conditions)

    def _is_rate_limit_issue(self, error_message: str) -> bool:
        rate_limit_keywords = [
            "429",
            "rate limit",
            "too many requests",
            "quota exceeded",
        ]
        return any(keyword in error_message.lower() for keyword in rate_limit_keywords)

    def _restart_driver(self, new_proxy=False):
        logger.info("Restarting WebDriver to clear memory/cache.")
        self.driver.quit()

        if new_proxy:
            self.driver = self._create_webdriver(use_proxy=True)
        else:
            self.driver = self._create_webdriver(self.use_proxy)

    def _create_webdriver(self, use_proxy: bool):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if use_proxy:
            proxy = FreeProxy(rand=True).get()
            logger.info(f"Using proxy: {proxy}")
            options.add_argument(f"--proxy-server={proxy}")

        # Correctly initialize the Chrome driver with options
        driver_path = ChromeDriverManager().install()
        service = Service(executable_path=driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def _check_memory_usage(self):
        memory = psutil.virtual_memory()
        available_memory_mb = memory.available / (1024 * 1024)
        memory_threshold_mb = available_memory_mb * (self.memory_threshold_percent / 100)
        logger.info(f"Available Memory: {available_memory_mb:.2f} MB")
        logger.info(f"Memory Threshold: {memory_threshold_mb:.2f} MB")
        return available_memory_mb < memory_threshold_mb

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def get_spotify_track_view_count(self, url: str) -> int:
        try:
            play_count_info = self.find_element_by_xpath(url, SPOTIFY_VIEW_COUNT_XPATH)

            if play_count_info == "Element not found on the page":
                if self.spotify_error_count == SPOTIFY_ERROR_THRESHOLD:
                    raise ValueError("Too many spotify errors, investigate")

                self.spotify_error_count += 1
                return 0

            if play_count_info:
                logger.info(f"original spotify play count value {play_count_info}")
                play_count = int(play_count_info.replace(",", ""))
                logger.info(play_count)
                return play_count

        except Exception as e:
            print(f"Error with xpath {SPOTIFY_VIEW_COUNT_XPATH}: {e}")

        raise ValueError(f"Could not find play count for {url}")


class CacheManager:
    def __init__(self, mongo_client: MongoDBClient, collection_name: str):
        self.mongo_client = mongo_client
        self.collection_name = collection_name
        self.cache = self.load_cache()

    def load_cache(self) -> dict:
        logger.info(f"Loading {self.collection_name} cache into memory")
        cache = {}
        data = self.mongo_client.get_collection(self.collection_name).find()
        for item in data:
            cache[item["key"]] = item["value"]
        return cache

    def get(self, key: str) -> Any:
        return self.cache.get(key)

    def set(self, key: str, value: Any) -> None:
        self.cache[key] = value
        self.mongo_client.get_collection(self.collection_name).update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True,
        )


def overwrite_collection(client, collection_name: str, documents: list[dict]) -> None:
    clear_collection(client, collection_name)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(insert_or_update_data_to_mongo, client, collection_name, doc)
            for doc in documents
        ]
        for future in futures:
            future.result()


def overwrite_kv_collection(client, collection_name: str, kv_dict: dict) -> None:
    clear_collection(client, collection_name)

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(insert_or_update_kv_data_to_mongo, client, collection_name, key, value)
            for key, value in kv_dict.items()
        ]
        for future in futures:
            future.result()
