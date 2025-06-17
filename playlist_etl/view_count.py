import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import requests
from requests.exceptions import RequestException
from tenacity import retry, stop_after_attempt, wait_exponential

from playlist_etl.helpers import get_logger, set_secrets
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
)

logger = get_logger(__name__)

AGGREGATED_DATA_COLLECTION = "aggregated_playlists"
VIEW_COUNTS_COLLECTION = "view_counts_playlists"
CURRENT_TIMESTAMP = datetime.now().isoformat()
SERVICE_NAMES = ["Spotify", "Youtube"]
SPOTIFY_VIEW_COUNT_XPATH = '(//*[contains(concat(" ", @class, " "), concat(" ", "w1TBi3o5CTM7zW1EB3Bm", " "))])[4]'
SPOTIFY_ERROR_COUNT = 0
SPOTIFY_ERROR_THRESHOLD = 5


def initialize_new_view_count_playlists(mongo_client: MongoClient) -> None:
    if collection_is_empty(VIEW_COUNTS_COLLECTION, mongo_client):
        aggregated_playlists = read_data_from_mongo(
            mongo_client, AGGREGATED_DATA_COLLECTION
        )
        for playlist in aggregated_playlists:
            insert_or_update_data_to_mongo(
                mongo_client, VIEW_COUNTS_COLLECTION, playlist
            )


def create_or_update_track(
    track: dict,
    service_name: str,
    current_view_count: int,
    current_timestamp: str,
) -> dict:
    if "view_count_data_json" not in track:
        track["view_count_data_json"] = defaultdict(dict)

    if "initial_count_json" not in track["view_count_data_json"][service_name]:
        track["view_count_data_json"][service_name]["initial_count_json"] = {
            "initial_timestamp": current_timestamp,
            "initial_view_count": current_view_count,
        }

    track["view_count_data_json"][service_name]["current_count_json"] = {
        "current_timestamp": current_timestamp,
        "current_view_count": current_view_count,
    }
    return track


def update_service_view_count(
    track: dict,
    service_name: str,
    spotify_client: Spotify,
    mongo_client: MongoClient,
    webdriver_manager: WebDriverManager,
) -> dict:
    service_url_key = f"{service_name}_url".lower()
    if service_url_key not in track or not track[service_url_key]:
        track[service_url_key] = get_service_url(
            service_name, track, spotify_client, mongo_client
        )

    current_view_count = get_view_count(track, service_name, webdriver_manager)
    return create_or_update_track(
        track, service_name, current_view_count, CURRENT_TIMESTAMP
    )


def update_view_counts(
    playlists: list[dict],
    mongo_client: MongoClient,
    webdriver_manager: WebDriverManager,
    spotify_client: Spotify,
    max_workers: int = 1,
):
    for playlist in playlists:
        logger.info(f"Updating view counts for {playlist['genre_name']}")
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


def get_view_count(
    track: dict, service_name: str, webdriver_manager: WebDriverManager
) -> int:
    match service_name:
        case "Spotify":
            return get_spotify_track_view_count(track["spotify_url"], webdriver_manager)
        case "Youtube":
            return get_youtube_track_view_count(track["youtube_url"])
        case _:
            raise ValueError("Unexpected service name")


def get_spotify_track_view_count(url: str, webdriver_manager: WebDriverManager) -> int:
    global SPOTIFY_ERROR_COUNT, SPOTIFY_ERROR_THRESHOLD
    try:
        logging.info(SPOTIFY_VIEW_COUNT_XPATH)
        play_count_info = webdriver_manager.find_element_by_xpath(
            url, SPOTIFY_VIEW_COUNT_XPATH
        )

        if play_count_info == "Element not found on the page":
            if SPOTIFY_ERROR_COUNT == SPOTIFY_ERROR_THRESHOLD:
                raise ValueError("Too many spotify errors, investigate")

            SPOTIFY_ERROR_COUNT += 1

            return 0

        if play_count_info:
            logger.info(f"original spotify play count value {play_count_info}")
            play_count = int(play_count_info.replace(",", ""))
            logger.info(play_count)
            return play_count

    except Exception as e:
        print(f"Error with xpath {SPOTIFY_VIEW_COUNT_XPATH}: {e}")

    raise ValueError(f"Could not find play count for {url}")


@retry(
    wait=wait_exponential(multiplier=1, min=4, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def get_youtube_track_view_count(youtube_url: str) -> int:
    video_id = youtube_url.split("v=")[-1]

    api_key = os.getenv("GOOGLE_API_KEY")
    youtube_api_url = f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"

    try:
        response = requests.get(youtube_api_url)
        response.raise_for_status()

        data = response.json()
        if data["items"]:
            view_count = data["items"][0]["statistics"]["viewCount"]
            logger.info(f"Video ID {video_id} has {view_count} views.")
            return int(view_count)
        else:
            logging.warning(f"No data found for video ID {video_id}")
            return 0
    except RequestException as e:
        logging.error(f"Request failed: {e}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            raise ValueError(
                f"Quota exceeded: Could not get view count for {youtube_url}"
            )
        raise ValueError(f"Failed to retrieve view count for {youtube_url}: {e}")
    except ValueError as e:
        logging.error(f"Value error: {e}")
        raise
    except Exception as e:
        logging.exception(f"An unexpected error occurred: {e}")
        raise ValueError(f"Unexpected error occurred for {youtube_url}: {e}")


def get_spotify_track_url_by_isrc(isrc: str, spotify_client: Spotify) -> str:
    logger.info(f"Searching for track with ISRC: {isrc}")
    results = spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
    tracks = results["tracks"]["items"]
    if tracks:
        track_id = tracks[0]["id"]
        track_url = f"https://open.spotify.com/track/{track_id}"
        logger.info(f"Found track URL: {track_url}")
        return track_url
    raise ValueError(f"Could not find track for ISRC: {isrc}")


if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    initialize_new_view_count_playlists(mongo_client)
    spotify_client = get_spotify_client()
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)
    webdriver_manager = WebDriverManager(use_proxy=False)
    update_view_counts(
        view_counts_playlists, mongo_client, webdriver_manager, spotify_client
    )
