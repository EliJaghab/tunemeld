import logging
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List

import requests
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from playlist_etl.transform import get_youtube_url_by_track_and_artist_name
from playlist_etl.utils import (
    MongoClient,
    Spotify,
    WebDriverManager,
    collection_is_empty,
    get_mongo_client,
    get_spotify_client,
    insert_or_update_data_to_mongo,
    read_data_from_mongo,
    set_secrets,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)

AGGREGATED_DATA_COLLECTION = "aggregated_playlists"
VIEW_COUNTS_COLLECTION = "view_counts_playlists"
CURRENT_TIMESTAMP = datetime.now().isoformat()
SERVICE_NAMES = ["Youtube"]
SPOTIFY_VIEW_COUNT_XPATH = "//span[contains(@class, 'encore-text') and contains(@class, 'encore-text-body-small') and contains(@class, 'RANLXG3qKB61Bh3') and @data-testid='playcount']"


def initialize_new_view_count_playlists(mongo_client: MongoClient) -> None:
    if collection_is_empty(VIEW_COUNTS_COLLECTION, mongo_client):
        aggregated_playlists = read_data_from_mongo(mongo_client, AGGREGATED_DATA_COLLECTION)
        for playlist in aggregated_playlists:
            insert_or_update_data_to_mongo(mongo_client, VIEW_COUNTS_COLLECTION, playlist)


def update_service_view_count(
    track: Dict,
    service_name: str,
    spotify_client: Spotify,
    mongo_client: MongoClient,
    webdriver_manager: WebDriverManager,
) -> Dict:
    service_url_key = f"{service_name}_url".lower()
    if service_url_key not in track or not track[service_url_key]:
        track[service_url_key] = get_service_url(service_name, track, spotify_client, mongo_client)

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

    initial_view_count = track["view_count_data_json"][service_name]["initial_count_json"][
        "initial_view_count"
    ]
    percentage_change = calculate_percentage_change(initial_view_count, current_view_count)
    track["view_count_data_json"][service_name]["percentage_change"] = percentage_change

    return track


def update_view_counts(
    playlists: List[Dict],
    mongo_client: MongoClient,
    webdriver_manager: WebDriverManager,
    spotify_client: Spotify,
    max_workers: int = 1,
):
    for playlist in playlists:
        logging.info(f"Updating view counts for {playlist['genre_name']}")
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = []
            for track in playlist["tracks"]:
                for service_name in SERVICE_NAMES:
                    future = executor.submit(
                        update_service_view_count,
                        track,
                        service_name,
                        spotify_client,
                        mongo_client,
                        webdriver_manager,
                    )
                    futures.append((future, track))

            for future, track in futures:
                updated_track = future.result()
                track.update(updated_track)

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
            return get_youtube_track_view_count(track["youtube_url"])
        case _:
            raise ValueError("Unexpected service name")


def get_spotify_track_view_count(url: str, webdriver_manager: WebDriverManager) -> int:
    try:
        play_count_info = webdriver_manager.find_element_by_xpath(url, SPOTIFY_VIEW_COUNT_XPATH)
        if play_count_info:
            play_count = int(play_count_info.replace(",", ""))
            logging.info(play_count)
            return play_count
    except Exception as e:
        print(f"Error with xpath {SPOTIFY_VIEW_COUNT_XPATH}: {e}")

    raise ValueError(f"Could not find play count for {url}")


def get_youtube_track_view_count(url: str, retries: int = 10, backoff_factor: float = 10) -> int:
    def fetch_view_count(url: str) -> int:
        response = requests.get(url)
        logging.debug(f"Received response with status code {response.status_code} for {url}")
        logging.debug(f"Response headers: {response.headers}")
        logging.debug(f"Response text: {response.text[:1000]}")  # Log the first 1000 characters of the response

        if response.status_code == 429:
            logging.error(f"Rate limited by YouTube for {url}. Status code: 429. Headers: {response.headers}")
            raise ValueError(f"Rate limited by YouTube for {url}")

        if response.status_code != 200:
            logging.error(f"Error fetching page content for {url}. Status code: {response.status_code}. Response text: {response.text[:1000]}")
            raise ValueError(f"Failed to fetch page content for {url}. Status code: {response.status_code}")

        soup = BeautifulSoup(response.text, "html.parser")
        view_count_tag = soup.find("meta", itemprop="interactionCount")
        if view_count_tag:
            view_count = int(view_count_tag.get("content"))
            logging.info(f"View count for {url}: {view_count}")
            return view_count

        logging.warning(f"Could not find play count tag for {url}")
        raise ValueError(f"Could not find play count for {url}")

    def exponential_backoff(attempt: int) -> float:
        return backoff_factor * (2 ** (attempt - 1))

    attempt = 0
    while attempt < retries:
        try:
            return fetch_view_count(url)
        except (RequestException, ValueError) as e:
            attempt += 1
            logging.warning(f"Attempt {attempt} failed for {url}: {e}")
            if attempt < retries:
                sleep_time = exponential_backoff(attempt)
                logging.info(f"Retrying in {sleep_time} seconds... (Attempt {attempt}/{retries})")
                time.sleep(sleep_time)
            else:
                logging.error(f"Fatal error: failed to retrieve view count after {retries} attempts for {url}")
                raise ValueError(f"Failed to retrieve view count after {retries} attempts for {url}")




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
    webdriver_manager = WebDriverManager(use_proxy=False)
    update_view_counts(view_counts_playlists, mongo_client, webdriver_manager, spotify_client)
