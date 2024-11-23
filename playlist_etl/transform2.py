import concurrent.futures
import os
from collections import defaultdict
from typing import Any

from playlist_etl.config import (
    RANK_PRIORITY,
    RAW_PLAYLISTS_COLLECTION,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
)
from playlist_etl.models import GenreName, Playlist, ServiceName, Track, TrackData, TrackRank
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import AppleMusicService, CacheService, SpotifyService, YouTubeService
from playlist_etl.utils import get_logger, set_secrets

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
            for service_name in ServiceName:
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
                service_name=ServiceName(service_name),
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
        self, data: dict, service_name: str, genre_name: str
    ) -> None:
        logger.info(f"Converting data to track objects for {service_name} and genre {genre_name}")
        if service_name == ServiceName.APPLE_MUSIC:
            self.convert_apple_music_raw_export_to_track_type(data, genre_name)
        elif service_name == ServiceName.SPOTIFY:
            self.convert_spotify_raw_export_to_track_type(data, genre_name)
        elif service_name == ServiceName.SOUNDCLOUD:
            self.convert_soundcloud_raw_export_to_track_type(data, genre_name)
        else:
            raise ValueError("Unknown service name")

    def get_track(
        self, isrc
    ) -> Track:
        if isrc in self.tracks:
            track = self.tracks[isrc]
        else:
            track = Track(isrc=isrc)
            self.tracks[isrc] = track
        return track

    def convert_apple_music_raw_export_to_track_type(
        self, data: dict, genre_name: str
    ) -> None:
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

                track_url = track_data["link"]
                album_cover_url = track_data.get("album_cover_url")
                track = self.get_track(isrc, track_name, artist_name, track_url, album_cover_url)
                track.apple_music_track_data = TrackData(
                    service_name=ServiceName.APPLE_MUSIC,
                    track_name=track_name,
                    artist_name=artist_name,
                    track_url=track_url,
                    album_cover_url=None,
                )

                self.playlist_ranks[(ServiceName.APPLE_MUSIC.value, genre_name)].append(
                    TrackRank(
                        isrc=isrc,
                        rank=int(key) + 1,
                        sources=[ServiceName.APPLE_MUSIC.value],
                    )
                )

    def convert_soundcloud_raw_export_to_track_type(
        self, data: dict, genre_name: str
    ) -> None:
        logger.info(f"Converting SoundCloud data for genre {genre_name}")
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

            track = self.get_track(isrc, track_name, artist_name, track_url, album_cover_url)
            track.soundcloud_track_data = TrackData(
                service_name=ServiceName.SOUNDCLOUD,
                track_name=track_name,
                artist_name=artist_name,
                track_url=track_url,
                album_cover_url=album_cover_url,
            )

            self.playlist_ranks[(ServiceName.SOUNDCLOUD.value, genre_name)].append(
                TrackRank(
                    isrc=isrc,
                    rank=i + 1,
                    sources=[ServiceName.SOUNDCLOUD.value],
                )
            )

    def convert_spotify_raw_export_to_track_type(
        self, data: dict, genre_name: str
    ) -> None:
        logger.info(f"Converting Spotify data for genre {genre_name}")
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

            track = self.get_track(isrc, track_name, artist_name, track_url, album_cover_url)
            track.spotify_track_data = TrackData(
                service_name=ServiceName.SPOTIFY,
                track_name=track_name,
                artist_name=artist_name,
                track_url=track_url,
                album_cover_url=album_cover_url,
            )

            self.playlist_ranks[(ServiceName.SPOTIFY.value, genre_name)].append(
                TrackRank(
                    isrc=isrc,
                    rank=i + 1,
                    sources=[ServiceName.SPOTIFY.value],
                )
            )

    def set_youtube_urls(self) -> None:
        logger.info("Setting YouTube URLs for all tracks")
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
            futures = [
                executor.submit(self.set_youtube_url, track) for track in self.tracks.values()
            ]
            concurrent.futures.wait(futures)

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
                if track.apple_music_track_data and not track.apple_music_track_data.album_cover_url
            ]
            concurrent.futures.wait(futures)

    def set_apple_music_album_cover_url(self, track: Track) -> None:
        if track.apple_music_track_data and not track.apple_music_track_data.album_cover_url:
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
            concurrent.futures.wait(futures)

    def set_spotify_url(self, track: Track) -> None:
        if not track.spotify_track_data.track_url:
            spotify_url = self.spotify_service.get_track_url_by_isrc(track.isrc)
            track.spotify_track_data.track_url = spotify_url
    
    def overwrite(self) -> None:
        logger.info("Saving transformed data to MongoDB")
        formatted_tracks = [
            {
                "isrc": isrc,
                "soundcloud_track_data": track.soundcloud_track_data.model_dump() if track.soundcloud_track_data else None,
                "spotify_track_data": track.spotify_track_data.model_dump() if track.spotify_track_data else None,
                "apple_music_track_data": track.apple_music_track_data.model_dump() if track.apple_music_track_data else None,
                "youtube_url": track.youtube_url,
                "spotify_views": track.spotify_views.model_dump() if track.spotify_views else None,
                "youtube_views": track.youtube_views.model_dump() if track.youtube_views else None,
            }
            for isrc, track in self.tracks.items()
            if track.isrc is not None
        ]
        formatted_ranks = self.format_playlist_ranks()
        self.mongo_client.overwrite_collection(TRACK_COLLECTION, formatted_tracks)
        self.mongo_client.overwrite_collection(TRACK_PLAYLIST_COLLECTION, formatted_ranks)


class Aggregate:
    def __init__(self, mongo_client: MongoDBClient):
        self.mongo_client = mongo_client

    def aggregate(self):
        track_playlists = self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION)
        candidates_by_genre = self._group_by_genre(track_playlists)
        matches = self._get_matches(candidates_by_genre)
        ranked_matches = self._add_aggregate_rank(matches)
        sorted_matches = self._rank_matches(ranked_matches)
        formatted_playlists = self._format_aggregated_playlist(sorted_matches)
        self._write_aggregated_playlists(formatted_playlists)

    def _group_by_genre(self, track_playlists) -> dict:
        """Group ISRC matches across the same genre from different services."""
        candidates_by_genre = defaultdict(lambda: defaultdict(dict))
        for genre_name in GENRE_NAMES:
            for service_name in SERVICE_NAMES:
                track_playlist = track_playlists.find_one(
                    {"genre_name": genre_name, "service_name": service_name}
                )
                if not track_playlist:
                    logger.warning(
                        f"No track playlist found for genre {genre_name} and service {service_name}"
                    )
                    continue

                for track in track_playlist["tracks"]:
                    candidates_by_genre[genre_name][track["isrc"]][track["service_name"]] = track[
                        "rank"
                    ]

        return candidates_by_genre

    def _get_matches(self, candidates: dict) -> dict:
        """Get ISRCs that come up more than once for the same genre."""
        matches = defaultdict(dict)
        for genre_name, isrcs in candidates.items():
            for isrc, sources in isrcs.items():
                if len(sources) > 1:
                    matches[genre_name][isrc] = sources
        return matches

    def _add_aggregate_rank(self, matches: dict) -> dict:
        """Rank matches based on the rank of the services."""
        for genre_name, isrc_sources in matches.items():
            for isrc, sources in isrc_sources.items():
                aggregate_service_name = None

                for service_name in RANK_PRIORITY:
                    if service_name in sources:
                        aggregate_service_name = service_name
                        break

                if aggregate_service_name:
                    raw_aggregate_rank = sources[aggregate_service_name]
                    sources["raw_aggregate_rank"] = raw_aggregate_rank
                    sources["aggregate_service_name"] = aggregate_service_name

        return matches

    def _rank_matches(self, matches: dict) -> dict:
        for genre_name, isrc_sources in matches.items():
            # Convert isrc_sources (dict) to list and sort
            sorted_sources = sorted(isrc_sources.values(), key=lambda x: x["raw_aggregate_rank"])
            # Assign new rank
            for i, sources in enumerate(sorted_sources, start=1):
                sources["rank"] = i
        return matches

    def _format_aggregated_playlist(self, matches_by_genre: dict) -> dict:
        formatted_playlists = {}
        for genre_name, isrc_sources in matches_by_genre.items():
            tracks = [
                {
                    "isrc": isrc,
                    "rank": sources["rank"],
                    "sources": list(sources.keys()),  # Extracting service names
                }
                for isrc, sources in isrc_sources.items()
            ]
            formatted_playlists[genre_name] = {
                "service_name": ServiceName.AGGREGATE.value,
                "genre_name": genre_name,
                "tracks": tracks,
            }
        return formatted_playlists

    def _write_aggregated_playlists(self, formatted_playlists: dict) -> None:
        logger.info("Writing aggregated playlists to MongoDB")
        for genre_name in GENRE_NAMES:
            playlist = formatted_playlists.get(genre_name)
            if not playlist:
                logger.warning(f"No aggregated playlist found for genre {genre_name}")
                continue
            self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION).update_one(
                {"service_name": ServiceName.AGGREGATE.value, "genre_name": genre_name},
                {"$set": playlist},
                upsert=True,
            )


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

    #aggregate = Aggregate(mongo_client)
    #aggregate.aggregate()
