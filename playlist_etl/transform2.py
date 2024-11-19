import concurrent.futures
import os
from collections import defaultdict

from pydantic import BaseModel

from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, CacheService, SpotifyService, YouTubeService
from playlist_etl.utils import get_logger, set_secrets
from playlist_etl.config import (
    RAW_PLAYLISTS_COLLECTION,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
)

MAX_THREADS = 100

logger = get_logger(__name__)


class Track(BaseModel):
    isrc: str
    spotify_track_name: str | None = None
    spotify_artist_name: str | None = None
    spotify_track_url: str | None = None
    soundcloud_track_name: str | None = None
    soundcloud_artist_name: str | None = None
    soundcloud_track_url: str | None = None
    apple_music_track_name: str | None = None
    apple_music_artist_name: str | None = None
    apple_music_track_url: str | None = None
    album_cover_url: str | None = None
    youtube_url: str | None = None

    def set_youtube_url(self, youtube_service):
        if not self.youtube_url:
            self.youtube_url = youtube_service.get_youtube_url(self.track_name, self.artist_name)

    def set_apple_music_album_cover_url(self, apple_music_service):
        if not self.album_cover_url and self.apple_music_track_url:
            self.album_cover_url = apple_music_service.get_album_cover_url(
                self.apple_music_track_url
            )

    def to_dict(self) -> dict:
        return self.model_dump()


class PlaylistRank(BaseModel):
    isrc: str
    rank: int


class Transform:
    """
    Transforms tracks from raw playlists to Track objects.
    Stores ISRC to track relationship with playlist ranks in MongoDB.

    """

    def __init__(
        self, mongo_client, cache_service, spotify_service, youtube_service, apple_music_service
    ):
        self.mongo_client = mongo_client
        self.cache_service = cache_service
        self.spotify_service = spotify_service
        self.youtube_service = youtube_service
        self.apple_music_service = apple_music_service
        self.tracks: dict[str, Track] = {}
        self.playlist_ranks: dict[str, dict[str, int]] = (
            {}
        )  # {service_name}_{genre_name}: {isrc: rank}}

    def transform(self):
        logger.info("Starting the transformation process")
        self.load_and_transform_data()
        self.save_transformed_data()
        logger.info("Transformation process completed successfully")

    def load_and_transform_data(self):
        self.load_raw_playlists()
        self.build_track_objects()

    def save_transformed_data(self):
        formatted_tracks = self.format_tracks()
        formatted_ranks = self.format_playlist_ranks()
        self.write_to_database(formatted_tracks, formatted_ranks)

    def write_to_database(self, tracks: dict, ranks: dict):
        logger.info("Saving transformed data to MongoDB")
        self.mongo_client.overwrite_kv_collection(TRACK_COLLECTION, tracks)
        self.mongo_client.overwrite_kv_collection(TRACK_PLAYLIST_COLLECTION, ranks)

    def load_raw_playlists(self) -> list[dict]:
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = self.mongo_client.read_data(RAW_PLAYLISTS_COLLECTION)
        logger.info(f"Found {len(raw_playlists)} playlists in MongoDB")
        return raw_playlists

    def build_track_objects(self):
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = self.mongo_client.read_data(RAW_PLAYLISTS_COLLECTION)
        logger.info(f"Found playlists from MongoDB: {len(raw_playlists)} documents found")

        for playlist_data in raw_playlists:
            genre_name = playlist_data["genre_name"]
            service_name = playlist_data["service_name"]

            logger.info(f"Processing playlist for genre {genre_name} from {service_name}")
            self.convert_to_track_objects(playlist_data["data_json"], service_name, genre_name)

        self.set_youtube_url_for_all_tracks()
        self.set_apple_music_album_cover_url_for_all_tracks()

    def format_tracks(self):
        formatted_tracks = {
            isrc: track.to_dict() for isrc, track in self.tracks.items() if track.isrc is not None
        }
        return formatted_tracks

    def format_playlist_ranks(self):
        formatted_ranks = {
            playlist: [PlaylistRank(isrc=isrc, rank=rank).dict() for isrc, rank in ranks.items()]
            for playlist, ranks in self.playlist_ranks.items()
        }
        return formatted_ranks

    def overwrite_data_to_mongo(self):
        formatted_tracks = self.format_tracks()
        self.mongo_client.overwrite_kv_collection(TRACK_COLLECTION, formatted_tracks)
        formatted_ranks = self.format_playlist_ranks()
        self.mongo_client.overwrite_kv_collection(TRACK_PLAYLIST_COLLECTION, formatted_ranks)

    def convert_to_track_objects(self, data: dict, service_name: str, genre_name: str) -> None:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        if service_name == "AppleMusic":
            self.convert_apple_music_raw_export_to_track_type(data, genre_name)
        elif service_name == "Spotify":
            self.convert_spotify_raw_export_to_track_type(data, genre_name)
        elif service_name == "SoundCloud":
            self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
        else:
            raise ValueError("Unknown service name")

    def convert_apple_music_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
        isrc_rank_map = {}

        for key, track_data in data["album_details"].items():
            if key.isdigit():
                track_name = track_data["name"]
                artist_name = track_data["artist"]
                isrc = self.spotify_service.get_isrc(track_name, artist_name)

                if isrc is None:
                    logger.warning(
                        f"ISRC not found for Apple Music track: {track_name} by {artist_name}"
                    )
                    continue

                track_url = track_data["link"]

                if isrc in self.tracks:
                    track = self.tracks[isrc]
                    track.apple_music_track_name = track_name
                    track.apple_music_artist_name = artist_name
                    track.apple_music_track_url = track_url
                else:
                    track = Track(
                        isrc=isrc,
                        apple_music_track_name=track_name,
                        apple_music_artist_name=artist_name,
                        apple_music_track_url=track_url,
                    )
                    self.tracks[isrc] = track

                isrc_rank_map[isrc] = int(key) + 1

        self.playlist_ranks[f"AppleMusic_{genre_name}"] = isrc_rank_map

    def convert_soundcloud_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        isrc_rank_map = {}

        for i, item in enumerate(data["tracks"]["items"]):
            isrc = item.get("publisher", {}).get("isrc")
            if isrc is None:
                track_name = item["title"]
                artist_name = item["user"]["name"]
                isrc = self.spotify_service.get_isrc(track_name, artist_name)
                if isrc is None:
                    logger.warning(
                        f"ISRC not found for SoundCloud track: {track_name} by {artist_name}"
                    )
                    continue
            else:
                track_name = item["title"]
                artist_name = item["user"]["name"]

            track_url = item["permalink"]
            album_cover_url = item["artworkUrl"]

            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)

            if isrc in self.tracks:
                track = self.tracks[isrc]
                track.soundcloud_track_name = track_name
                track.soundcloud_artist_name = artist_name
                track.soundcloud_track_url = track_url
                track.album_cover_url = album_cover_url
            else:
                track = Track(
                    isrc=isrc,
                    soundcloud_track_name=track_name,
                    soundcloud_artist_name=artist_name,
                    soundcloud_track_url=track_url,
                    album_cover_url=album_cover_url,
                )
                self.tracks[isrc] = track

            isrc_rank_map[isrc] = i + 1

        self.playlist_ranks[f"SoundCloud_{genre_name}"] = isrc_rank_map

    def convert_spotify_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting Spotify data for genre {genre_name}")
        isrc_rank_map = {}
        for i, item in enumerate(data["items"]):
            track_info = item.get("track")

            if not track_info:
                continue

            track_name = track_info["name"]
            artist_name = ", ".join(artist["name"] for artist in track_info["artists"])
            track_url = track_info["external_urls"]["spotify"]
            album_cover_url = track_info["album"]["images"][0]["url"]
            isrc = track_info["external_ids"].get("isrc")

            if isrc is None:
                isrc = self.spotify_service.get_isrc(track_name, artist_name)
                if isrc is None:
                    logger.warning(
                        f"ISRC not found for Spotify track: {track_name} by {artist_name}"
                    )
                    continue

            if isrc in self.tracks:
                track = self.tracks[isrc]
                track.spotify_track_name = track_name
                track.spotify_artist_name = artist_name
                track.spotify_track_url = track_url
                track.album_cover_url = album_cover_url
            else:
                track = Track(
                    isrc=isrc,
                    spotify_track_name=track_name,
                    spotify_artist_name=artist_name,
                    spotify_track_url=track_url,
                    album_cover_url=album_cover_url,
                )
                self.tracks[isrc] = track

            isrc_rank_map[isrc] = i + 1

        self.playlist_ranks[f"Spotify_{genre_name}"] = isrc_rank_map

    def set_youtube_url_for_all_tracks(self) -> None:
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_youtube_url, self.youtube_service)
                for track in self.tracks.values()
            ]
            concurrent.futures.wait(futures)

    def set_apple_music_album_cover_url_for_all_tracks(self):
        logger.info("Setting Apple Music album cover URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_apple_music_album_cover_url, self.apple_music_service)
                for track in self.tracks.values()
                if track.apple_music_track_url
            ]
            concurrent.futures.wait(futures)


class Aggregate:
    def __init__(self, mongo_client):
        self.mongo_client = mongo_client

    def aggregate(self):
        tracks, track_playlist = self._get_track_data_from_mongo()
        self._aggregate_tracks_by_isrc(track_playlist)

    def _aggregate_tracks_by_isrc(self, track_playlist):
        candidates_by_genre = self._group_by_genre(track_playlist)
        aggregate_by_isrc = self._group_by_isrc_within_genre(candidates_by_genre)
        matches = self._get_matches(aggregate_by_isrc)
        self._rank_matches(matches)

    def _get_track_data_from_mongo(self):
        tracks = self.mongo_client.read_data(TRACK_COLLECTION)
        track_playlist = self.mongo_client.read_data(TRACK_PLAYLIST_COLLECTION)
        return tracks, track_playlist

    def _group_by_genre(self, track_playlist) -> dict:
        """Group ISRC matches across the same genre from different services.
        Eg. output
        {
            "dance": {
                "23490580": {
                    "rank": 1,
                    "service_name": "soundcloud"
                },
                "23490580": {
                    "rank": 2,
                    "service_name": "spotify"
                }
            }
        }
        """
        candidates_by_genre = defaultdict(dict)
        for item in track_playlist:
            genre_name, service_name = item["key"].split("_")
            for track in item["value"]:
                candidates_by_genre[genre_name][track["isrc"]] = {
                    "rank": track["rank"],
                    "service_name": service_name,
                }
        return candidates_by_genre

    def _group_by_isrc_within_genre(self, candidate_by_genre):
        """Groups ISRC matches across the same genre. Two different playlists can have the same ISRC.
        Eg. output
        {
            "dance": {
                "23490580": {
                    [("soundcloud", 1)]
                },
                "23434580": {
                    [("soundcloud", 1), ("spotify", 2)]
                }
            }
            "pop": {
                "23490523": {
                    [("soundcloud", 1), ("spotify", 2)]
                },
                "23490580": {
                    [("soundcloud", 1)]
                }
        }
        """
        aggregate_by_isrc = defaultdict(lambda: defaultdict(list))
        for genre, candidates in candidate_by_genre.items():
            for isrc, candidate in candidates.items():
                aggregate_by_isrc[genre][isrc].append(
                    (candidate["service_name"], candidate["rank"])
                )
        return aggregate_by_isrc

    def _get_matches(self, aggregate_by_isrc):
        """Get ISRCs that come up more than once for the same genre.
        Eg. input
         {
            "pop": {
                "23490523": {
                    [("soundcloud", 1), ("spotify", 2)]
                },
                "23490580": {
                    [("soundcloud", 1)]
                }
        }
        Eg. output:
        {
            "pop": {
                "23490523": {
                    [("soundcloud", 1), ("spotify", 2)]
        }
        """
        matches = {}
        for genre, isrcs in aggregate_by_isrc.items():
            matches[genre] = {isrc: sources for isrc, sources in isrcs.items() if len(sources) > 1}
        return matches

    def _rank_matches(self, matches):
        """Rank matches based on the rank of the services.
        Eg. input
        {
            "pop": {
                "23490523": {
                    [("soundcloud", 1), ("spotify", 2)]
                },
        }
        Eg. output
        {
            "dance": {
                1: {
                    ISRC: "23490523",
                    sources: [("soundcloud", 1), ("spotify", 2)]
                }
            }
        }
        """
        rank_priority = ["AppleMusic", "SoundCloud", "Spotify"]
        for genre_name, matches_by_genre in matches.items():
            for isrc, sources in matches_by_genre.items():
                ranked_sources = sorted(sources, key=lambda x: rank_priority.index(x[0]))
                matches[genre_name][isrc] = {"isrc": isrc, "sources": ranked_sources}

        return matches


if __name__ == "__main__":
    set_secrets()
    mongo_client = MongoDBClient()
    cache_service = CacheService(mongo_client)
    spotify_service = SpotifyService(
        client_id=os.getenv("SPOTIFY_CLIENT_ID"),
        client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
        cache_service=cache_service,
    )
    youtube_service = YouTubeService(
        api_key=os.getenv("GOOGLE_API_KEY"), cache_service=cache_service
    )
    apple_music_service = AppleMusicService(cache_service)

    transform = Transform(
        mongo_client, cache_service, spotify_service, youtube_service, apple_music_service
    )
    transform.transform()

    aggregate = Aggregate(mongo_client)
    aggregate.aggregate()
