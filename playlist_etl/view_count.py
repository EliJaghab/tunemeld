import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from transform import get_youtube_url_by_track_and_artist_name
from utils import (
    MongoClient,
    Spotify,
    WebDriverManager,
    clear_collection,
    collection_is_empty,
    get_mongo_client,
    get_spotify_client,
    insert_or_update_data_to_mongo,
    read_data_from_mongo,
    set_secrets,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


AGGREGATED_DATA_COLLECTION = "aggregated_playlists"
VIEW_COUNTS_COLLECTION = "view_counts_playlists"
CURRENT_TIMESTAMP = datetime.now().isoformat()
SERVICE_NAMES = ["Spotify", "Youtube"]


def initialize_new_view_count_playlists(mongo_client: MongoClient) -> None:
    if collection_is_empty(VIEW_COUNTS_COLLECTION, mongo_client):
        aggregated_playlists = read_data_from_mongo(mongo_client, AGGREGATED_DATA_COLLECTION)
        for playlist in aggregated_playlists:
            insert_or_update_data_to_mongo(mongo_client, VIEW_COUNTS_COLLECTION, playlist)


def update_view_counts(
    playlists: List[Dict],
    mongo_client: MongoClient,
    webdriver_manager: WebDriverManager,
    spotify_client: Spotify,
):
    for playlist in playlists:
        logging.info(f"updating view counts for {playlist['genre_name']}")
        for track in playlist["tracks"]:

            for service_name in SERVICE_NAMES:
                service_url_key = f"{service_name}_url".lower()
                if not service_url_key in track or not track[service_url_key]:
                    track[service_url_key] = get_service_url(
                        service_name, track, spotify_client, mongo_client
                    )

                if "view_count_data_json" not in track:
                    track["view_count_data_json"] = defaultdict(dict)

                current_view_count = get_view_count(track, service_name, webdriver_manager)
                if "initial_count_json" not in track["view_count_data_json"][service_name]:
                    track["view_count_data_json"][service_name]["initial_count_json"] = {
                        "initial_timestamp": CURRENT_TIMESTAMP,
                        "initial_view_count": current_view_count,
                    }

                track["view_count_data_json"][service_name]["current_count_json"] = {
                    "current_timestamp": CURRENT_TIMESTAMP,
                    "current_view_count": current_view_count,
                }

                initial_view_count = track["view_count_data_json"][service_name][
                    "initial_count_json"
                ]["initial_view_count"]
                percentage_change = calculate_percentage_change(
                    initial_view_count, current_view_count
                )
                track["view_count_data_json"][service_name]["percentage_change"] = percentage_change

        insert_or_update_data_to_mongo(mongo_client, VIEW_COUNTS_COLLECTION, playlist)


def get_service_url(
    service_name: str,
    track: dict,
    spotify_client: Spotify,
    mongo_client: MongoClient,
):
    match service_name:
        case "Spotify":
            return get_spotify_track_url_by_isrc(track["isrc"], spotify_client)
        case "Youtube":
            return get_youtube_url_by_track_and_artist_name(
                track["track_name"], track["artist_name"], mongo_client
            )
        case _:
            raise ValueError("Unexpected service name")


def get_view_count(track: dict, service_name: str, webdriver_manager: WebDriverManager) -> int:
    match service_name:
        case "Spotify":
            return get_spotify_track_view_count(track["spotify_url"], webdriver_manager)
        case "Youtube":
            return get_youtube_track_view_count(track["youtube_url"], webdriver_manager)
        case _:
            raise ValueError("Unexpected service name")


def get_spotify_track_view_count(url: str, webdriver_manager: WebDriverManager) -> int:
    xpath = "//*[contains(concat( ' ', @class, ' ' ), concat( ' ', 'RANLXG3qKB61Bh33I0r2', ' '' ))]"
    play_count_info = find_element_by_xpath(url, xpath, webdriver_manager)
    if not play_count_info:
        raise ValueError(f"Could not find play count for {url}")
    play_count = int(play_count_info.replace(",", ""))
    return play_count


def get_youtube_track_view_count(url: str, webdriver_manager: WebDriverManager) -> int:
    response = requests.get(url)
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch page content for {url}")

    soup = BeautifulSoup(response.text, "html.parser")
    view_count_tag = soup.find("meta", itemprop="interactionCount")
    if view_count_tag:
        return int(view_count_tag.get("content"))
    raise ValueError(f"Could not get view count for url {url}")


def get_spotify_track_url_by_isrc(isrc: str, spotify_client: Spotify) -> str:
    logging.info(f"Searching for track with ISRC: {isrc}")
    results = spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
    tracks = results["tracks"]["items"]
    if tracks:
        track_id = tracks[0]["id"]
        track_url = f"https://open.spotify.com/track/{track_id}"
        logging.info(f"Found track URL: {track_url}")
        return track_url
    raise ValueError(f"Could not find track for ISRC: {isrc}")


def find_element_by_xpath(
    url: str,
    xpath: str,
    webdriver_manager: WebDriverManager,
    retries: int = 2,
    retry_delay: int = 2,
) -> str:
    logging.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")

    def attempt_find_element() -> str:
        try:
            driver.implicitly_wait(2)
            logging.info(f"Navigating to URL: {url}")
            webdriver_manager.get(url)

            timeout = 5
            max_timeout = 15
            start_time = time.time()

            while time.time() - start_time < max_timeout:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
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

    driver = webdriver_manager.get_driver()
    result = attempt_find_element(driver)
    if "An error occurred" in result or result in [
        "Timed out waiting for element",
        "Element not found on the page",
        "Element not found",
    ]:
        logging.info("Initial attempt failed, retrying with proxy")
        webdriver_manager.reset_driver(use_proxy=True)

        attempt = 1
        while attempt < retries:
            driver = webdriver_manager.get_driver()
            result = attempt_find_element(driver)

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

            logging.info(f"Retrying with proxy... (attempt {attempt+1} of {retries})")
            time.sleep(retry_delay)
            attempt += 1

    return result


def calculate_percentage_change(initial_count: int, current_count: int) -> float:
    if initial_count == 0:
        return 0.0
    return ((current_count - initial_count) / initial_count) * 100


if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    initialize_new_view_count_playlists(mongo_client)
    spotify_client = get_spotify_client()
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)
    webdriver_manager = WebDriverManager()
    update_view_counts(view_counts_playlists, mongo_client, webdriver_manager, spotify_client)
    webdriver_manager.close_driver()
