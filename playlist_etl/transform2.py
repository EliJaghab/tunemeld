import concurrent.futures
import os
from collections import defaultdict
from typing import Any

from pydantic import BaseModel

from playlist_etl.config import (
    APPLE_MUSIC,
    GENRE_NAMES,
    RANK_PRIORITY,
    RAW_PLAYLISTS_COLLECTION,
    SERVICE_NAMES,
    SOUNDCLOUD,
    SPOTIFY,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
)
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, CacheService, SpotifyService, YouTubeService
from playlist_etl.utils import get_logger, set_secrets

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

    def set_youtube_url(self, youtube_service: YouTubeService) -> None:
        if not self.youtube_url:
            self.youtube_url = youtube_service.get_youtube_url(self.track_name, self.artist_name)

    def set_apple_music_album_cover_url(self, apple_music_service: AppleMusicService) -> None:
        if not self.album_cover_url and self.apple_music_track_url:
            self.album_cover_url = apple_music_service.get_album_cover_url(
                self.apple_music_track_url
            )


class TrackRank(BaseModel):
    isrc: str
    rank: int
    sources: list[str]


class PlaylistRank(BaseModel):
    service_name: str
    genre_name: str
    tracks: list[TrackRank]


class Transform:
    """
    Transforms tracks from raw playlists to Track objects.
    Stores ISRC to track relationship with playlist ranks in MongoDB.
    """

    def __init__(
        self,
        mongo_client: MongoDBClient,
        cache_service: CacheService,
        spotify_service: SpotifyService,
        youtube_service: YouTubeService,
        apple_music_service: AppleMusicService,
    ):
        self.mongo_client = mongo_client
        self.cache_service = cache_service
        self.spotify_service = spotify_service
        self.youtube_service = youtube_service
        self.apple_music_service = apple_music_service
        self.tracks: dict[str, Track] = {}
        self.playlist_ranks: dict[tuple[str, str], list[TrackRank]] = {}

    def transform(self) -> None:
        logger.info("Starting the transformation process")
        self.build_track_objects()
        self.overwrite()
        logger.info("Transformation process completed successfully")

    def overwrite(self) -> None:
        logger.info("Saving transformed data to MongoDB")
        formatted_tracks = self.format_tracks()
        formatted_ranks = self.format_playlist_ranks()
        self.mongo_client.overwrite_collection(TRACK_COLLECTION, formatted_tracks)
        self.mongo_client.overwrite_collection(TRACK_PLAYLIST_COLLECTION, formatted_ranks)

    def build_track_objects(self) -> None:
        logger.info("Reading raw playlists from MongoDB")
        raw_playlists = self.mongo_client.get_collection(RAW_PLAYLISTS_COLLECTION)

        for genre_name in GENRE_NAMES:
            for service_name in SERVICE_NAMES:
                raw_playlist = raw_playlists.find_one(
                    {"genre_name": genre_name, "service_name": service_name}
                )
                logger.info(f"Processing playlist for genre {genre_name} from {service_name}")
                self.convert_to_track_objects(raw_playlist["data_json"], service_name, genre_name)

        self.set_youtube_url_for_all_tracks()
        self.set_apple_music_album_cover_url_for_all_tracks()

    def format_tracks(self) -> list[dict[str, Any]]:
        formatted_tracks = [
            {"isrc": isrc, "service_data": track.model_dump(exclude={"isrc"})}
            for isrc, track in self.tracks.items()
            if track.isrc is not None
        ]
        return formatted_tracks

    def format_playlist_ranks(self) -> list[dict[str, Any]]:
        formatted_ranks = [
            PlaylistRank(
                service_name=service_name,
                genre_name=genre_name,
                tracks=[
                    TrackRank(isrc=rank.isrc, rank=rank.rank, sources=rank.sources)
                    for rank in ranks
                ],
            ).model_dump()
            for (service_name, genre_name), ranks in self.playlist_ranks.items()
        ]
        return formatted_ranks

    def convert_to_track_objects(
        self, data: dict[str, Any], service_name: str, genre_name: str
    ) -> None:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        if service_name == APPLE_MUSIC:
            self.convert_apple_music_raw_export_to_track_type(data, genre_name)
        elif service_name == SPOTIFY:
            self.convert_spotify_raw_export_to_track_type(data, genre_name)
        elif service_name == SOUNDCLOUD:
            self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
        else:
            raise ValueError("Unknown service name")

    def convert_apple_music_raw_export_to_track_type(
        self, data: dict[str, Any], genre_name: str
    ) -> None:
        logger.info(f"Converting Apple Music data for genre {genre_name}")
        isrc_rank_map = []

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

                isrc_rank_map.append(TrackRank(isrc=isrc, rank=int(key) + 1, sources=[APPLE_MUSIC]))

        self.playlist_ranks[(APPLE_MUSIC, genre_name)] = isrc_rank_map

    def convert_soundcloud_raw_export_to_track_type(
        self, data: dict[str, Any], genre_name: str
    ) -> None:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
        isrc_rank_map = []

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

            isrc_rank_map.append(TrackRank(isrc=isrc, rank=i + 1, sources=[SOUNDCLOUD]))

        self.playlist_ranks[(SOUNDCLOUD, genre_name)] = isrc_rank_map

    def convert_spotify_raw_export_to_track_type(
        self, data: dict[str, Any], genre_name: str
    ) -> None:
        logger.info(f"Converting Spotify data for genre {genre_name}")
        isrc_rank_map = []
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

            isrc_rank_map.append(TrackRank(isrc=isrc, rank=i + 1, sources=[SPOTIFY]))

        self.playlist_ranks[(SPOTIFY, genre_name)] = isrc_rank_map

    def set_youtube_url_for_all_tracks(self) -> None:
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_youtube_url, self.youtube_service)
                for track in self.tracks.values()
            ]
            concurrent.futures.wait(futures)

    def set_apple_music_album_cover_url_for_all_tracks(self) -> None:
        logger.info("Setting Apple Music album cover URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(track.set_apple_music_album_cover_url, self.apple_music_service)
                for track in self.tracks.values()
                if track.apple_music_track_url
            ]
            concurrent.futures.wait(futures)


class Aggregate:
    def __init__(self, mongo_client: MongoDBClient):
        self.mongo_client = mongo_client

    def aggregate(self, track_playlist):
        candidates_by_genre = self._group_by_genre(track_playlist)
        matches = self._get_matches(candidates_by_genre)
        self._rank_matches(matches)

    def _group_by_genre(self, track_playlist) -> dict:
        """Group ISRC matches across the same genre from different services.
        Eg. output
        {
            "dance": {
                "23490580": {
                    "SoundCloud": 1,
                    "Spotify": 2
                }
            }
        }
        """
        track_playlists = self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION)
        candidates_by_genre = defaultdict(lambda: defaultdict(dict))
        for genre_name in GENRE_NAMES:
            for service_name in SERVICE_NAMES:
                track_playlist = track_playlists.find_one(
                    {"genre_name": genre_name, "service_name": service_name}
                )

                for track in track_playlist["tracks"]:
                    candidates_by_genre[genre_name][track["isrc"]][service_name] = track["rank"]

        return candidates_by_genre

    def _get_matches(self, candidates):
        """Get ISRCs that come up more than once for the same genre."""
        matches = defaultdict(dict)
        for genre_name, isrc in candidates.items():
            for isrc, sources in isrc.items():
                if len(sources.values()) > 1:
                    matches[genre_name][isrc] = sources
        return matches

    def _rank_by_service(self, matches):
        """Rank matches based on the rank of the services."""
        for isrc_sources in matches.values():
            for sources in isrc_sources.values():
                aggregate_service_name = None

                for service_name in RANK_PRIORITY:
                    if service_name in sources:
                        aggregate_service_name = service_name

                raw_aggregate_rank = sources[aggregate_service_name]
                sources["raw_aggregate_rank"] = raw_aggregate_rank
                sources["aggregate_service_name"] = aggregate_service_name

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
    # aggregate.aggregate()
