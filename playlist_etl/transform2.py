import concurrent.futures
from collections import defaultdict

from playlist_etl.config import (
    RAW_PLAYLISTS_COLLECTION,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
)
from playlist_etl.helpers import get_logger
from playlist_etl.models import GenreName, Playlist, Track, TrackRank, TrackSourceServiceName
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, SpotifyService, YouTubeService

MAX_THREADS = 100

logger = get_logger(__name__)


class Transform:
    """
    Converts raw tracks to Track Object
    Converts raw playlists to Playlist Object.
    """

    def __init__(
        self,
        mongo_client: MongoDBClient,
        spotify_service: SpotifyService,
        youtube_service: YouTubeService,
        apple_music_service: AppleMusicService,
    ):
        self.mongo_client = mongo_client
        self.spotify_service = spotify_service
        self.youtube_service = youtube_service
        self.apple_music_service = apple_music_service
        self.tracks: dict[str, Track] = {}
        self.playlist_ranks: defaultdict[tuple[str, str], list[TrackRank]] = defaultdict(list)

    def transform(self) -> None:
        logger.info("Starting the transformation process")
        raw_playlists = self.mongo_client.get_collection(RAW_PLAYLISTS_COLLECTION)
        self.build_track_objects(raw_playlists)
        self.set_youtube_urls()
        self.set_apple_music_album_covers()
        self.set_spotify_urls()
        self.overwrite()
        logger.info("Transformation process completed successfully")

    def build_track_objects(self, raw_playlists: dict) -> None:
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = self.mongo_client.get_collection(RAW_PLAYLISTS_COLLECTION)

        for genre_name in GenreName:
            for service_name in TrackSourceServiceName:
                genre_name_value = genre_name.value
                service_name_value = service_name.value

                raw_playlist = raw_playlists.find_one(
                    {"genre_name": genre_name_value, "service_name": service_name_value}
                )
                logger.info(
                    f"Processing playlist for genre {genre_name_value} from {service_name_value}"
                )
                self.convert_to_track_objects(
                    raw_playlist["data_json"], service_name_value, genre_name_value
                )

    def format_tracks(self) -> list[dict]:
        formatted_tracks = [
            {"isrc": isrc, "track_data": track.model_dump(exclude={"isrc"})}
            for isrc, track in self.tracks.items()
            if track.isrc is not None
        ]
        return formatted_tracks

    def format_playlist_ranks(self) -> list[dict]:
        formatted_ranks = [
            Playlist(
                service_name=TrackSourceServiceName(service_name),
                genre_name=genre_name,
                tracks=[
                    TrackRank(isrc=rank.isrc, rank=rank.rank, sources=rank.sources)
                    for rank in ranks
                ],
            ).model_dump()
            for (service_name, genre_name), ranks in self.playlist_ranks.items()
        ]
        return formatted_ranks

    def convert_to_track_objects(self, data: dict, service_name: str, genre_name: str) -> None:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        if service_name == TrackSourceServiceName.APPLE_MUSIC:
            self.convert_apple_music_raw_export_to_track_type(data, genre_name)
        elif service_name == TrackSourceServiceName.SPOTIFY:
            self.convert_spotify_raw_export_to_track_type(data, genre_name)
        elif service_name == TrackSourceServiceName.SOUNDCLOUD:
            self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
        else:
            raise ValueError("Unknown service name")

    def get_track(self, isrc: str) -> Track:
        if isrc in self.tracks:
            track = self.tracks[isrc]
        else:
            track = Track(isrc=isrc)
            self.tracks[isrc] = track
        return track

    def convert_apple_music_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
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

                track = self.get_track(isrc)
                track.apple_music_track_data.track_name = track_name
                track.apple_music_track_data.artist_name = artist_name
                track.apple_music_track_data.track_url = track_data["link"]

                self.playlist_ranks[(TrackSourceServiceName.APPLE_MUSIC.value, genre_name)].append(
                    TrackRank(
                        isrc=isrc,
                        rank=int(key) + 1,
                        sources={TrackSourceServiceName.APPLE_MUSIC: int(key) + 1},
                    )
                )

    def convert_soundcloud_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        for i, item in enumerate(data["tracks"]["items"]):
            isrc = item["publisher"]["isrc"]
            if not isrc:
                continue

            track_name = item["title"]
            artist_name = item["user"]["name"]

            if " - " in track_name:
                artist_name, track_name = track_name.split(" - ", 1)

            track = self.get_track(isrc)
            track.soundcloud_track_data.track_name = track_name
            track.soundcloud_track_data.artist_name = artist_name
            track.soundcloud_track_data.track_url = item["permalink"]
            track.soundcloud_track_data.album_cover_url = item["artworkUrl"]

            self.playlist_ranks[(TrackSourceServiceName.SOUNDCLOUD.value, genre_name)].append(
                TrackRank(
                    isrc=isrc,
                    rank=i + 1,
                    sources={TrackSourceServiceName.SOUNDCLOUD: i + 1},
                )
            )

    def convert_spotify_raw_export_to_track_type(self, data: dict, genre_name: str) -> None:
        logger.info(f"Converting Spotify data for genre {genre_name}")
        for i, item in enumerate(data["items"]):
            track_info = item["track"]
            if not track_info:
                continue
            isrc = track_info["external_ids"]["isrc"]

            track = self.get_track(isrc)
            track.spotify_track_data.track_name = track_info["name"]
            track.spotify_track_data.artist_name = ", ".join(
                artist["name"] for artist in track_info["artists"]
            )
            track.spotify_track_data.track_url = track_info["external_urls"]["spotify"]
            track.spotify_track_data.album_cover_url = track_info["album"]["images"][0]["url"]

            self.playlist_ranks[(TrackSourceServiceName.SPOTIFY.value, genre_name)].append(
                TrackRank(
                    isrc=isrc,
                    rank=i + 1,
                    sources={TrackSourceServiceName.SPOTIFY: i + 1},
                )
            )

    def set_youtube_urls(self) -> None:
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(self.set_youtube_url, track) for track in self.tracks.values()
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def set_youtube_url(self, track: Track) -> None:
        if not track.youtube_url:
            youtube_url = self.youtube_service.get_youtube_url(
                track.spotify_track_data.track_name
                or track.soundcloud_track_data.track_name
                or track.apple_music_track_data.track_name,
                track.spotify_track_data.artist_name
                or track.soundcloud_track_data.artist_name
                or track.apple_music_track_data.artist_name,
            )
            track.youtube_url = youtube_url

    def set_apple_music_album_covers(self) -> None:
        logger.info("Setting Apple Music album cover URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(self.set_apple_music_album_cover_url, track)
                for track in self.tracks.values()
                if track.apple_music_track_data
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def set_apple_music_album_cover_url(self, track: Track) -> None:
        if track.apple_music_track_data.track_name:
            album_cover_url = self.apple_music_service.get_album_cover_url(
                track.apple_music_track_data.track_url
            )
            track.apple_music_track_data.album_cover_url = album_cover_url

    def set_spotify_urls(self) -> None:
        logger.info("Setting Spotify URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(self.set_spotify_url, track)
                for track in self.tracks.values()
                if not track.spotify_track_data.track_url
            ]
            for future in concurrent.futures.as_completed(futures):
                future.result()

    def set_spotify_url(self, track: Track) -> None:
        if not track.spotify_track_data.track_url:
            spotify_url = self.spotify_service.get_track_url_by_isrc(track.isrc)
            track.spotify_track_data.track_url = spotify_url

    def merge_track_data(self, existing_data: dict, new_data: dict) -> dict:
        def recursive_merge(d1: dict, d2: dict) -> dict:
            for key, value in d2.items():
                if isinstance(value, dict) and key in d1 and isinstance(d1[key], dict):
                    d1[key] = recursive_merge(d1[key], value)
                else:
                    d1[key] = value
            return d1

        return recursive_merge(existing_data.copy(), new_data)

    def overwrite(self) -> None:
        logger.info("Saving transformed data to MongoDB")
        formatted_tracks = [
            {
                "isrc": isrc,
                "soundcloud_track_data": (
                    track.soundcloud_track_data.model_dump()
                    if track.soundcloud_track_data
                    else None
                ),
                "spotify_track_data": (
                    track.spotify_track_data.model_dump() if track.spotify_track_data else None
                ),
                "apple_music_track_data": (
                    track.apple_music_track_data.model_dump()
                    if track.apple_music_track_data
                    else None
                ),
                "youtube_url": track.youtube_url,
                "spotify_views": track.spotify_views.model_dump() if track.spotify_views else None,
                "youtube_views": track.youtube_views.model_dump() if track.youtube_views else None,
            }
            for isrc, track in self.tracks.items()
            if track.isrc is not None
        ]
        formatted_ranks = self.format_playlist_ranks()

        track_collection = self.mongo_client.get_collection(TRACK_COLLECTION)
        for track in formatted_tracks:
            existing_track = track_collection.find_one({"isrc": track["isrc"]})
            if existing_track:
                merged_track = self.merge_track_data(existing_track, track)
                track_collection.update_one(
                    {"isrc": track["isrc"]}, {"$set": merged_track}, upsert=True
                )
            else:
                track_collection.update_one({"isrc": track["isrc"]}, {"$set": track}, upsert=True)

        self.mongo_client.overwrite_collection(TRACK_PLAYLIST_COLLECTION, formatted_ranks)
