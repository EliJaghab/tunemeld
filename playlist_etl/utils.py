import logging
import os
import time
from datetime import datetime, timezone
from queue import Queue
from threading import Lock

import psutil
from dotenv import load_dotenv
from fp.fp import FreeProxy
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
    def __init__(self, use_proxy=False, memory_threshold_percent=75):
        self.use_proxy = use_proxy
        self.memory_threshold_percent = memory_threshold_percent
        self.visits_counter = 0
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
        memory_threshold_mb = available_memory_mb * (self.memory_threshold_percent / 100)
        logging.info(f"Available Memory: {available_memory_mb:.2f} MB")
        logging.info(f"Memory Threshold: {memory_threshold_mb:.2f} MB")
        return available_memory_mb < memory_threshold_mb

    def find_element_by_xpath(
        self, url: str, xpath: str, attribute: str = None, retries: int = 5, retry_delay: int = 10
    ) -> str:
        def _attempt_find_element() -> str:
            try:
                self.driver.implicitly_wait(2)
                logging.info(f"Navigating to URL: {url}")
                self.driver.get(url)

                timeout = 5
                max_timeout = 15
                start_time = time.time()

                while time.time() - start_time < max_timeout:
                    try:
                        element = self.driver.find_element(By.XPATH, xpath)
                        if element and element.is_displayed():
                            if attribute:
                                element_value = element.get_attribute(attribute)
                                logging.info(
                                    f"Successfully found element attribute: {element_value}"
                                )
                                return element_value
                            else:
                                element_text = element.text
                                logging.info(f"Successfully found element text: {element_text}")
                                return element_text
                    except NoSuchElementException:
                        logging.info("Element not found yet, retrying...")
                        time.sleep(0.5)

                logging.warning("Element not found even after waiting")
                return "Element not found"

            except TimeoutException:
                logging.error("Timed out waiting for element")
                return "Timed out waiting for element"
            except NoSuchElementException:
                logging.error("Element not found on the page")
                return "Element not found on the page"
            except Exception as e:
                logging.error(f"An error occurred: {str(e)}")
                return f"An error occurred: {str(e)}"

        logging.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")

        result = _attempt_find_element()
        if "An error occurred" in result or result in [
            "Timed out waiting for element",
            "Element not found on the page",
            "Element not found",
        ]:
            logging.info("Initial attempt failed, retrying with proxy")
            self._restart_driver()

            attempt = 1
            while attempt < retries:
                result = _attempt_find_element()

                if not (
                    "An error occurred" in result
                    or result
                    in [
                        "Timed out waiting for element",
                        "Element not found on the page",
                        "Element not found",
                    ]
                ):
                    return result

                logging.info(f"Retrying with proxy... (attempt {attempt + 1} of {retries})")
                time.sleep(retry_delay)
                attempt += 1

        return result

    def close_driver(self):
        if self.driver:
            self.driver.quit()
