import logging
import os
import time
from datetime import datetime, timezone
from queue import Queue
from threading import Lock

from dotenv import load_dotenv
from fp.fp import FreeProxy
import psutil
from pymongo import MongoClient
from selenium import webdriver
from selenium.common.exceptions import (
    InvalidSelectorException,
    NoSuchElementException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from spotipy import Spotify
from spotipy.oauth2 import SpotifyClientCredentials

PLAYLIST_ETL_COLLECTION_NAME = "playlist_etl"

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def set_secrets():
    if not os.getenv("GITHUB_ACTIONS"):
        env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
        logging.info("env_path" + env_path)
        load_dotenv(dotenv_path=env_path)


def get_mongo_client():
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri:
        raise Exception("MONGO_URI environment variable not set")
    return MongoClient(mongo_uri)


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
            logging.info(f"Data updated for id: {document['_id']}")
            return

    document["insert_timestamp"] = datetime.now(timezone.utc)
    result = collection.insert_one(document)
    logging.info(f"Data inserted with id: {result.inserted_id}")


def read_cache_from_mongo(mongo_client, collection_name):
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    collection = db[collection_name]
    cache = {}
    for item in collection.find():
        cache[item["key"]] = item["value"]
    return cache


def update_cache_in_mongo(mongo_client, collection_name, key, value):
    logging.info(
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
    logging.info(f"Cleared collection: {collection_name}")


def collection_is_empty(collection_name, mongo_client) -> bool:
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME]
    return not read_data_from_mongo(mongo_client, collection_name)


class WebDriverManager:
    def __init__(self, use_proxy=False, max_visits=15, memory_threshold_percent=75):
        self.use_proxy = use_proxy
        self.max_visits = max_visits
        self.memory_threshold_percent = memory_threshold_percent
        self.visits_counter = 0
        self.lock = Lock()
        self.driver = self._create_webdriver(use_proxy)

    def _create_webdriver(self, use_proxy: bool):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")

        if use_proxy:
            proxy = FreeProxy(rand=True).get()
            logging.info(f"Using proxy: {proxy}")
            options.add_argument(f"--proxy-server={proxy}")

        driver = webdriver.Chrome(options=options)
        return driver

    def _restart_driver(self):
        logging.info("Restarting WebDriver to clear memory/cache.")
        self.driver.quit()
        self.driver = self._create_webdriver(self.use_proxy)
        self.visits_counter = 0

    def _check_memory_usage(self):
        memory = psutil.virtual_memory()
        available_memory_mb = memory.available / (1024 * 1024)
        memory_threshold_mb = (available_memory_mb * (self.memory_threshold_percent / 100))
        logging.info(f"Available Memory: {available_memory_mb:.2f} MB")
        logging.info(f"Memory Threshold: {memory_threshold_mb:.2f} MB")
        return available_memory_mb < memory_threshold_mb

    def find_element_by_xpath(
        self, url: str, xpath: str, attribute: str = None, retries: int = 5, retry_delay: int = 10
    ) -> str:
        logging.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")

        if self.visits_counter >= self.max_visits or self._check_memory_usage():
            self._restart_driver()

        try:
            logging.info(f"Navigating to URL: {url}")
            self.driver.get(url)
            self.visits_counter += 1

            wait = WebDriverWait(self.driver, 10)
            element = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))

            if attribute:
                return element.get_attribute(attribute)
            else:
                return element.text

        except (NoSuchElementException, TimeoutException) as e:
            logging.warning(f"Element not found: {str(e)}")
            return "Element not found"

        except InvalidSelectorException as e:
            logging.error(f"Invalid selector: {str(e)}")
            return f"An error occurred: {str(e)}"

        except WebDriverException as e:
            logging.error(f"WebDriverException occurred: {str(e)}")
            return f"WebDriver error occurred: {str(e)}"

        except Exception as e:
            logging.error(f"An unexpected error occurred: {str(e)}")
            return f"An unexpected error occurred: {str(e)}"

    def close_driver(self):
        if self.driver:
            self.driver.quit()