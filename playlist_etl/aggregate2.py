from collections import defaultdict

from playlist_etl.config import (
    TRACK_PLAYLIST_COLLECTION,
)
from playlist_etl.config import RANK_PRIORITY
from playlist_etl.models import TrackSourceServiceName, GenreName, PlaylistType
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.helpers import get_logger

logger = get_logger(__name__)


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
        for genre_name in GenreName:
            for service_name in TrackSourceServiceName:
                track_playlist = track_playlists.find_one(
                    {"genre_name": genre_name, "service_name": service_name}
                )

                for track in track_playlist["tracks"]:
                    candidates_by_genre[genre_name][track["isrc"]][service_name] = track[
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
        for isrc_sources in matches.values():
            for sources in isrc_sources.values():
                aggregate_service_name = None

                for service_name in RANK_PRIORITY:
                    if service_name in sources:
                        aggregate_service_name = service_name
                        break

                raw_aggregate_rank = sources[aggregate_service_name]
                sources["raw_aggregate_rank"] = raw_aggregate_rank
                sources["aggregate_service_name"] = aggregate_service_name

        return matches

    def _rank_matches(self, matches: dict) -> dict:
        for isrc_sources in matches.values():
            sorted_sources = sorted(isrc_sources.values(), key=lambda x: x["raw_aggregate_rank"])
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
                    "sources": sources
                }
                for isrc, sources in isrc_sources.items()
            ]
            tracks.sort(key=lambda x: x["rank"])
            formatted_playlists[genre_name] = {
                "service_name": PlaylistType.AGGREGATE.value,
                "genre_name": genre_name,
                "tracks": tracks,
            }
        return formatted_playlists

    def _write_aggregated_playlists(self, formatted_playlists: dict) -> None:
        logger.info("Writing aggregated playlists to MongoDB")
        for genre_name in GenreName:
            genre_name = genre_name.value
            playlist = formatted_playlists[genre_name]
            self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION).update_one(
                {"service_name": PlaylistType.AGGREGATE.value, "genre_name": genre_name},
                {"$set": playlist},
                upsert=True,
            )
