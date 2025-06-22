"""
Transform playlist metadata from raw extraction to clean, formatted strings

This module takes the enhanced metadata attributes extracted from playlist pages
and transforms them into clean, user-friendly strings for display.

Focus: Spotify playlist metadata transformation
"""

import re
from datetime import datetime
from typing import TypedDict

from playlist_etl.config import PLAYLIST_METADATA_COLLECTION, RAW_PLAYLISTS_COLLECTION
from playlist_etl.extract import PlaylistMetadata
from playlist_etl.helpers import get_logger
from playlist_etl.mongo_db_client import MongoDBClient

logger = get_logger(__name__)


class DisplayPlaylistMetadata(TypedDict, total=False):
    """Type definition for display-ready playlist metadata"""
    service_name: str
    genre_name: str
    playlist_name: str
    playlist_url: str
    playlist_cover_url: str | None
    playlist_cover_description_text: str
    playlist_featured_artist: str | None
    raw_metadata: PlaylistMetadata
    last_transformed: str | None


def transform_playlist_name(raw_name: str) -> str:
    """Clean and format playlist name"""
    if not raw_name or raw_name == "Unknown":
        return "Untitled Playlist"

    # Remove any trailing metadata that might have leaked in
    cleaned = re.sub(r"\s*\|\s*Spotify.*$", "", raw_name)
    return cleaned.strip()


def transform_playlist_tagline(raw_tagline: str | None) -> str | None:
    """Clean and format playlist tagline/description"""
    if not raw_tagline:
        return None

    # Remove common artifacts
    cleaned = raw_tagline.strip()

    # Remove "Cover: Artist" part if present
    if "Cover:" in cleaned:
        cleaned = cleaned.split("Cover:")[0].strip()

    # Remove trailing "Spotify" or similar artifacts
    cleaned = re.sub(r"\s*Spotify\s*.*$", "", cleaned)

    # Remove any trailing numbers that might be saves counts, followers, etc.
    cleaned = re.sub(r"\s*\d+[,\d]*\s*(saves?|likes?|followers?)\s*.*$", "", cleaned)

    # Remove any remaining trailing words commonly found in artifacts
    cleaned = re.sub(r"\s*(premium|plus|free|followers?|likes?|saves?)\s*$", "", cleaned, flags=re.IGNORECASE)

    # Clean up extra whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    # Ensure proper capitalization and punctuation
    if cleaned and not cleaned.endswith("."):
        cleaned += "."

    return cleaned if cleaned else None


def transform_featured_artist(raw_artist: str | None) -> str | None:
    """Clean and format featured artist name"""
    if not raw_artist:
        return None

    # Remove any trailing metadata
    cleaned = re.sub(r"\s*\d+[,\d]*\s*(saves?|likes?|followers?)\s*.*$", "", raw_artist)
    cleaned = re.sub(r"\s*Spotify\s*.*$", "", cleaned)

    # Clean up common artifacts
    cleaned = cleaned.strip()

    return cleaned if cleaned else None




def transform_creator(raw_creator: str | None) -> str:
    """Transform creator info into display format"""
    if not raw_creator:
        return "Spotify"

    # If it's a URL, extract the username
    if raw_creator.startswith("http"):
        # Extract from URLs like "https://open.spotify.com/user/spotify"
        match = re.search(r"/user/([^/?]+)", raw_creator)
        if match:
            username = match.group(1)
            return username.replace("_", " ").title()

    return raw_creator or "Spotify"


def _create_fallback_description(tagline: str | None, featured_artist: str | None) -> str:
    """Create a fallback description when none exists"""
    if tagline:
        return tagline

    if featured_artist:
        return f"Cover: {featured_artist}"

    raise ValueError("No valid playlist description found - missing tagline, featured artist, and description content")




def transform_spotify_playlist_metadata(raw_metadata: PlaylistMetadata) -> DisplayPlaylistMetadata:
    """Transform all playlist metadata fields"""
    # Transform individual fields
    clean_tagline = transform_playlist_tagline(raw_metadata.get("playlist_tagline"))
    clean_featured_artist = transform_featured_artist(raw_metadata.get("playlist_featured_artist"))

    # Create description text with Cover: artist if present
    description_parts = []
    if clean_tagline:
        description_parts.append(clean_tagline)
    if clean_featured_artist:
        description_parts.append(f"Cover: {clean_featured_artist}")

    # Final description text
    if description_parts:
        playlist_cover_description_text = " ".join(description_parts)
    else:
        playlist_cover_description_text = _create_fallback_description(clean_tagline, clean_featured_artist)

    transformed = {
        "service_name": "Spotify",
        "genre_name": raw_metadata.get("genre_name"),
        "playlist_url": raw_metadata.get("playlist_url"),
        "playlist_cover_url": raw_metadata.get("playlist_cover_url"),
        "playlist_cover_description_text": playlist_cover_description_text,
        "playlist_featured_artist": clean_featured_artist,

        # Keep original data for reference
        "raw_metadata": raw_metadata,
        "last_transformed": None  # Will be set by transform process
    }

    return transformed


def process_spotify_playlist_metadata(genre_name: str) -> None:
    """Transform Spotify playlist metadata for a specific genre"""
    logger.info(f"Transforming Spotify playlist metadata for {genre_name}")

    mongo_client = MongoDBClient()

    try:
        # Get raw Spotify playlist data for the genre
        collection = mongo_client.get_collection(RAW_PLAYLISTS_COLLECTION)
        raw_playlists = list(collection.find({"service_name": "Spotify", "genre_name": genre_name}))

        for raw_playlist in raw_playlists:
            logger.info(f"Transforming metadata for playlist: {raw_playlist.get('playlist_name')}")

            # Transform the metadata
            transformed = transform_spotify_playlist_metadata(raw_playlist)

            # Update the raw playlist with transformed description
            collection.update_one(
                {"_id": raw_playlist["_id"]},
                {"$set": {"playlist_cover_description_text": transformed["playlist_cover_description_text"]}}
            )

            logger.info(f"Updated playlist with transformed description: {raw_playlist.get('playlist_name')}")

    except Exception as e:
        logger.error(f"Error transforming Spotify playlist metadata: {e}")
        raise




def transform_all_spotify_metadata() -> None:
    """Transform metadata for all Spotify playlists across all genres"""
    from playlist_etl.extract import PLAYLIST_GENRES

    logger.info("Starting transformation of all Spotify playlist metadata")

    for genre in PLAYLIST_GENRES:
        try:
            process_spotify_playlist_metadata(genre)
        except Exception as e:
            logger.error(f"Failed to transform metadata for {genre}: {e}")
            continue

    logger.info("Completed transformation of all Spotify playlist metadata")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        genre = sys.argv[1]
        process_spotify_playlist_metadata(genre)
    else:
        transform_all_spotify_metadata()
