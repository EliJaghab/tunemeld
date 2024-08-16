import logging
import os
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List

import requests

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
SERVICE_NAMES = ["Spotify", "Youtube"]
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


def get_youtube_track_view_count(youtube_url: str) -> int:
    video_id = youtube_url.split("v=")[-1]

    api_key = os.getenv("GOOGLE_API_KEY")
    youtube_api_url = (
        f"https://www.googleapis.com/youtube/v3/videos?part=statistics&id={video_id}&key={api_key}"
    )

    response = requests.get(youtube_api_url)

    if response.status_code == 200:
        data = response.json()
        if data["items"]:
            view_count = data["items"][0]["statistics"]["viewCount"]
            logging.info(f"Video ID {video_id} has {view_count} views.")
            return int(view_count)
        else:
            logging.info(f"No data found for video ID {video_id}")
            return 0
    else:
        logging.error(f"Error: {response.status_code}, {response.text}")
        if response.status_code == 403 and "quotaExceeded" in response.text:
            raise ValueError(f"Quota exceeded: Could not get view count for {youtube_url}")
        raise ValueError(f"Failed to retrieve view count for {youtube_url}")


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

if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    initialize_new_view_count_playlists(mongo_client)
    spotify_client = get_spotify_client()
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)
    webdriver_manager = WebDriverManager(use_proxy=False)
    update_view_counts(view_counts_playlists, mongo_client, webdriver_manager, spotify_client)
