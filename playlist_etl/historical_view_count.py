import logging
from datetime import datetime
from typing import Dict, List

from pymongo import MongoClient

from playlist_etl.utils import (
    get_mongo_client,
    read_data_from_mongo,
    set_secrets,
    PLAYLIST_ETL_COLLECTION_NAME
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s() - %(message)s",
)

VIEW_COUNTS_COLLECTION = "view_counts_playlists"
TRACK_VIEWS_COLLECTION = "track_views"
CURRENT_TIMESTAMP = datetime.now().isoformat()

def create_historical_view_counts(
    view_counts: List[Dict],
    mongo_client: MongoClient
):
    historical_view_counts = {}

    for playlist in view_counts:
        for track in playlist["tracks"]:
            isrc = track.get("isrc")
            if not isrc:
                logging.warning(f"Track with name {track.get('track_name')} has no ISRC. Skipping.")
                continue

            for service_name, view_count_data in track.get("view_count_data_json", {}).items():
                if isrc not in historical_view_counts:
                    historical_view_counts[isrc] = {}

                if service_name not in historical_view_counts[isrc]:
                    historical_view_counts[isrc][service_name] = []

                # Only append the current count
                current_count = view_count_data.get("current_count_json")
                if current_count:
                    historical_view_counts[isrc][service_name].append({
                        "timestamp": current_count["current_timestamp"],
                        "view_count": current_count["current_view_count"]
                    })

    insert_historical_view_counts_to_mongo(historical_view_counts, mongo_client)

def insert_historical_view_counts_to_mongo(
    historical_view_counts: Dict[str, Dict[str, List[Dict[str, int]]]],
    mongo_client: MongoClient
):
    db = mongo_client[PLAYLIST_ETL_COLLECTION_NAME] 
    collection = db[TRACK_VIEWS_COLLECTION]  

    for isrc, services in historical_view_counts.items():
        update_data = {"isrc": isrc}

        for service_name, view_data in services.items():
            update_data[f"view_counts.{service_name}"] = view_data

        collection.update_one(
            {"isrc": isrc},
            {"$set": update_data},
            upsert=True
        )

    logging.info("All historical view counts have been updated in MongoDB.")

if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()

    # Read the view counts from the view_counts_playlists collection
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)

    # Create historical view counts
    create_historical_view_counts(view_counts_playlists, mongo_client)
