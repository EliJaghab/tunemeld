import logging
from datetime import datetime
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from pymongo import MongoClient
from pymongo.collection import Collection

from utils import (
    set_secrets,
    get_mongo_client,
    get_mongo_collection,
    read_data_from_mongo,
)

HISTORICAL_TRACK_VIEWS_COLLECTION = "historical_track_views"
VIEW_COUNTS_COLLECTION = "view_counts_playlists"
CURRENT_TIMESTAMP = datetime.now().isoformat()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)


def get_all_tracks(mongo_client: MongoClient) -> List[Dict]:
    """Fetch all tracks from the playlists."""
    logging.info("Reading data from MongoDB.")
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)
    all_tracks = [
        track for playlist in view_counts_playlists for track in playlist["tracks"]
    ]
    logging.info(f"Retrieved {len(all_tracks)} tracks.")
    return all_tracks


def get_previous_view_count(
    isrc: str, service_name: str, historical_collection: Collection
) -> int:
    """Fetch the most recent view count for a given ISRC and service."""
    logging.debug(
        f"Fetching previous view count for ISRC: {isrc}, Service: {service_name}"
    )
    result = historical_collection.find_one(
        {"isrc": isrc}, projection={f"view_counts.{service_name}": {"$slice": -1}}
    )

    if result and service_name in result["view_counts"]:
        return result["view_counts"][service_name][-1]["view_count"]

    return 0


def update_historical_view_count(
    historical_collection: Collection,
    isrc: str,
    service_name: str,
    current_view_count: int,
    delta_count: int,
):
    """Update historical view count in MongoDB."""
    logging.debug(
        f"Updating historical view count for ISRC: {isrc}, Service: {service_name}"
    )
    new_reading = {
        "current_timestamp": CURRENT_TIMESTAMP,
        "view_count": current_view_count,
        "delta_count": delta_count,
    }

    result = historical_collection.update_one(
        {"isrc": isrc},
        {
            "$push": {
                f"view_counts.{service_name}": {
                    "$each": [new_reading],
                    "$sort": {"current_timestamp": -1},
                }
            },
            "$setOnInsert": {"isrc": isrc, "first_seen": CURRENT_TIMESTAMP},
        },
        upsert=True,
    )
    if result.modified_count > 0 or result.upserted_id:
        logging.info(
            f"Updated historical view count for ISRC: {isrc}, Service: {service_name}"
        )
    else:
        logging.info(f"No update performed for ISRC: {isrc}, Service: {service_name}")


def process_track(track: Dict, historical_collection: Collection) -> None:
    """Process a single track's view counts."""
    isrc = track["isrc"]
    for service_name, service_data in track["view_count_data_json"].items():
        current_view_count = service_data["current_count_json"]["current_view_count"]
        previous_view_count = get_previous_view_count(
            isrc, service_name, historical_collection
        )
        delta_count = current_view_count - previous_view_count
        update_historical_view_count(
            historical_collection, isrc, service_name, current_view_count, delta_count
        )


def process_tracks(tracks: List[Dict], mongo_client: MongoClient) -> None:
    """Process all tracks with concurrency."""
    historical_collection = get_mongo_collection(
        mongo_client, HISTORICAL_TRACK_VIEWS_COLLECTION
    )

    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(process_track, track, historical_collection): track
            for track in tracks
        }

        for future in as_completed(futures):
            future.result()


if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    tracks = get_all_tracks(mongo_client)
    process_tracks(tracks, mongo_client)
    logging.info("Completed processing all tracks.")
