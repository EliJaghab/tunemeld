import collections

from extract import PLAYLIST_GENRES
from helpers import set_secrets
from utils import (
    clear_collection,
    get_mongo_client,
    insert_or_update_data_to_mongo,
    read_data_from_mongo,
)
from view_count import VIEW_COUNTS_COLLECTION

AGGREGATED_DATA_COLLECTION = "aggregated_playlists"
TRANSFORMED_DATA_COLLECTION = "transformed_playlists"


def aggregate_tracks_by_isrc(services):
    track_aggregate = collections.defaultdict(dict)

    for service in services:
        for track in service["tracks"]:
            isrc = track["isrc"]
            source = track["source_name"]
            track_aggregate[isrc][source] = track

    filtered_aggregate = {}
    for isrc, sources in track_aggregate.items():
        if len(sources) > 1:
            filtered_aggregate[isrc] = sources

    return filtered_aggregate


def consolidate_tracks(tracks_by_isrc):
    consolidated_tracks = []

    rank_priority = ["AppleMusic", "SoundCloud", "Spotify"]
    default_source_priority = ["SoundCloud", "AppleMusic", "Spotify"]

    for track in tracks_by_isrc.values():
        primary_rank_source = next(
            (rank_source for rank_source in rank_priority if rank_source in track), None
        )
        primary_source = next(
            (source for source in default_source_priority if source in track), None
        )

        new_track_entry = track[primary_source].copy()
        new_track_entry["rank"] = track[primary_rank_source]["rank"]
        new_track_entry["additional_sources"] = {
            source: details["track_url"] for source, details in track.items()
        }

        consolidated_tracks.append(new_track_entry)

    consolidated_tracks.sort(key=lambda x: x["rank"])

    for index, track in enumerate(consolidated_tracks, start=1):
        track["rank"] = index

    return consolidated_tracks


def read_transformed_data_from_mongo(client, genre: str) -> list[dict]:
    print(f"Reading transformed data for genre: {genre} from MongoDB...")
    data = read_data_from_mongo(client, TRANSFORMED_DATA_COLLECTION)
    filtered_data = [doc for doc in data if doc["genre_name"] == genre]
    print(f"Found {len(filtered_data)} documents for genre: {genre}.")
    return filtered_data


if __name__ == "__main__":
    print("Setting secrets...")
    set_secrets()
    mongo_client = get_mongo_client()

    print(f"Clearing collection: {AGGREGATED_DATA_COLLECTION}")
    clear_collection(mongo_client, AGGREGATED_DATA_COLLECTION)

    for genre in PLAYLIST_GENRES:
        print(f"Processing genre: {genre}...")
        transformed_data = read_transformed_data_from_mongo(mongo_client, genre)
        tracks_by_isrc = aggregate_tracks_by_isrc(transformed_data)
        consolidated_tracks = consolidate_tracks(tracks_by_isrc)
        document = {
            "service_name": "aggregated",
            "genre_name": genre,
            "tracks": consolidated_tracks,
        }
        insert_or_update_data_to_mongo(
            mongo_client, AGGREGATED_DATA_COLLECTION, document
        )
        print(f"Aggregation and consolidation completed for genre: {genre}.")

    clear_collection(mongo_client, VIEW_COUNTS_COLLECTION)
