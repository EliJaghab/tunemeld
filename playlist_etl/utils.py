import os
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from typing import Any

from fp.fp import FreeProxy
from pymongo import MongoClient
from pymongo.collection import Collection
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials
from webdriver_manager.chrome import ChromeDriverManager

from playlist_etl.config import SPOTIFY_VIEW_COUNT_XPATH
from playlist_etl.helpers import get_logger
from playlist_etl.models import HistoricalView
from playlist_etl.mongo_db_client import MongoDBClient

PLAYLIST_ETL_COLLECTION_NAME = "playlist_etl"

logger = get_logger(__name__)

RETRIES = 3
RETRY_DELAY = 8


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
        client_credentials_manager=SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    )
    return spotify


def insert_or_update_data_to_mongo(client, collection_name, document):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
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


def insert_or_update_kv_data_to_mongo(client, collection_name, key, value):
    db = client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    existing_document = collection.find_one({"key": key})

    if existing_document:
        update_data = {"key": key, "value": value, "update_timestamp": datetime.now(timezone.utc)}
        collection.replace_one({"key": key}, update_data)
        logger.info(f"KV data updated for key: {key}")
    else:
        insert_data = {"key": key, "value": value, "insert_timestamp": datetime.now(timezone.utc)}
        collection.insert_one(insert_data)
        logger.info(f"KV data inserted with key: {key}")


def read_cache_from_mongo(mongo_client, collection_name):
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    cache = {}
    for item in collection.find():
        cache[item["key"]] = item["value"]
    return cache


def update_cache_in_mongo(mongo_client, collection_name, key, value):
    logger.info(f"Updating cache in collection: {collection_name} for key: {key} with value: {value}")
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
    return not read_data_from_mongo(mongo_client, collection_name)


class WebDriverManager:
    def __init__(self, use_proxy=False, memory_threshold_percent=75):
        self.use_proxy = use_proxy
        self.memory_threshold_percent = memory_threshold_percent
        self.driver = self._create_webdriver(self.use_proxy)
        self.spotify_error_count = 0

    def _create_webdriver(self, use_proxy: bool):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-web-security")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--remote-debugging-port=9222")

        # Additional options for GitHub Actions environment
        if os.getenv("GITHUB_ACTIONS"):
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")
            options.add_argument("--disable-images")
            options.add_argument("--disable-javascript")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--single-process")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-renderer-backgrounding")

        if use_proxy:
            proxy = FreeProxy(rand=True).get()
            logger.info(f"Using proxy: {proxy}")
            options.add_argument(f"--proxy-server={proxy}")

        try:
            # In GitHub Actions, try to use the system-installed chromedriver first
            if os.getenv("GITHUB_ACTIONS"):
                try:
                    # Try to use the chromedriver set up by the GitHub Action
                    service = Service()  # Use system chromedriver
                    logger.info("Using system chromedriver from GitHub Actions setup")
                    driver = webdriver.Chrome(service=service, options=options)
                    return driver
                except Exception as gha_e:
                    logger.warning(f"System chromedriver failed in GitHub Actions: {gha_e}")
                    # Fall back to ChromeDriverManager

            # Let ChromeDriverManager automatically handle version matching
            driver_path = ChromeDriverManager().install()

            # Make sure the driver is executable
            import stat

            current_perms = os.stat(driver_path).st_mode
            os.chmod(driver_path, current_perms | stat.S_IEXEC)

            service = Service(executable_path=driver_path)
            logger.info(f"Creating new WebDriver instance using path {driver_path}")
            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as e:
            logger.error(f"Failed to create WebDriver with auto-managed driver: {e}")
            # Fallback to system chromedriver if available
            try:
                service = Service()  # Use system chromedriver
                logger.info("Attempting to use system chromedriver as fallback")
                driver = webdriver.Chrome(service=service, options=options)
                return driver
            except Exception as fallback_e:
                logger.error(f"Fallback to system chromedriver also failed: {fallback_e}")
                raise RuntimeError(
                    f"Could not initialize ChromeDriver. Auto-managed error: {e}, System fallback error: {fallback_e}"
                ) from fallback_e

    def find_element_by_xpath(
        self,
        url: str,
        xpath: str,
        attribute: str | None = None,
    ) -> str:
        def _attempt_find_element() -> str:
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
            logger.warning("Element not found even after waiting")
            raise NoSuchElementException("Element not found")

        logger.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")
        return self._retry_with_backoff(RETRIES, RETRY_DELAY, _attempt_find_element)

    def _retry_with_backoff(self, retries: int, retry_delay: int, action):
        attempt = 1
        while attempt <= retries:
            try:
                result = action()
                return result
            except Exception as e:
                error_message = str(e)

                if isinstance(e, NoSuchElementException):
                    logger.error("Element not found: Unable to locate the specified element.")
                else:
                    logger.error(f"An error occurred: {error_message}")

                if self._is_rate_limit_issue(error_message):
                    logger.info("Rate limit detected, switching proxy and retrying...")
                    self._restart_driver(new_proxy=True)
                else:
                    logger.info(f"Retrying... (attempt {attempt} of {retries})")

                if attempt == retries:
                    raise
                time.sleep(retry_delay * (2 ** (attempt - 1)))
                attempt += 1

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
        self.driver = self._create_webdriver(use_proxy=new_proxy or self.use_proxy)

    def close_driver(self):
        if self.driver:
            self.driver.quit()

    def get_spotify_track_view_count(self, url: str, xpath: str = SPOTIFY_VIEW_COUNT_XPATH) -> int:
        try:
            play_count_info = self.find_element_by_xpath(url, xpath)
            if play_count_info:
                logger.info(f"Original Spotify play count value: {play_count_info}")
                play_count = int(play_count_info.replace(",", ""))
                logger.info(play_count)
                return play_count
        except Exception as e:
            logger.error(f"Error with XPath {xpath}: {e}")
            raise ValueError(f"Could not find play count for {url}") from e


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
        logger.info(f"Getting cache for key: {key} in collection: {self.collection_name}")
        return self.cache.get(key)

    def _validate_cache_entry(self, key: str, value: Any) -> bool:
        if key is None or value is None:
            raise ValueError("Key or value cannot be None")

    def set(self, key: str, value: Any) -> None:
        self._validate_cache_entry(key, value)
        logger.info(f"Setting cache for key: {key} with value: {value} in collection: {self.collection_name}")
        self.cache[key] = value
        self.mongo_client.get_collection(self.collection_name).update_one(
            {"key": key},
            {"$set": {"value": value}},
            upsert=True,
        )


def overwrite_collection(client, collection_name: str, documents: list[dict]) -> None:
    clear_collection(client, collection_name)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(insert_or_update_data_to_mongo, client, collection_name, doc) for doc in documents]
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


def get_delta_view_count(historical_views: list[HistoricalView], current_view_count: int) -> int:
    if not historical_views:
        return 0
    return current_view_count - historical_views[-1].total_view_count
