import concurrent.futures
import os

from pydantic import BaseModel

from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, CacheService, SpotifyService, YouTubeService
from playlist_etl.utils import get_logger, set_secrets

RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"

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
            self.album_cover_url = apple_music_service.get_album_cover_url(self.apple_music_track_url)

    def to_dict(self) -> dict:
        return self.dict()

    @property
    def track_name(self) -> str | None:
        return self.spotify_track_name or self.soundcloud_track_name or self.apple_music_track_name

    @property
    def artist_name(self) -> str | None:
        return self.spotify_artist_name or self.soundcloud_artist_name or self.apple_music_artist_name


class PlaylistRank(BaseModel):
    isrc: str
    rank: int


class Transform:
    """
    Transforms tracks from raw playlists to Track objects.
    Stores ISRC to track relationship with playlist ranks in MongoDB.

    """

    def __init__(self):
        set_secrets()
        self.mongo_client = MongoDBClient()
        self.cache_service = CacheService(self.mongo_client)

        self.spotify_service = SpotifyService(
            client_id=os.getenv("SPOTIFY_CLIENT_ID"),
            client_secret=os.getenv("SPOTIFY_CLIENT_SECRET"),
            cache_service=self.cache_service,
        )

        self.youtube_service = YouTubeService(
            api_key=os.getenv("GOOGLE_API_KEY"), cache_service=self.cache_service
        )

        self.apple_music_service = AppleMusicService(self.cache_service)

        self.tracks: dict[str, Track] = {}
        self.playlist_ranks: dict[str, dict[str, int]] = {}

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


if __name__ == "__main__":
    transform = Transform()
    transform.transform()
