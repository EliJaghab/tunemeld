from collections import defaultdict
from typing import Any

from pymongo.collection import Collection

from playlist_etl.config import RANK_PRIORITY, TRACK_PLAYLIST_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.models import (
    GenreName,
    Playlist,
    PlaylistType,
    TrackRank,
    TrackSourceServiceName,
)
from playlist_etl.mongo_db_client import MongoDBClient

logger = get_logger(__name__)


class Aggregate:
    def __init__(self, mongo_client: MongoDBClient) -> None:
        self.mongo_client = mongo_client

    def aggregate(self) -> None:
        track_playlists = self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION)
        candidates_by_genre = self._group_by_genre(track_playlists)
        matches = self._get_matches(candidates_by_genre)
        ranked_matches = self._add_aggregate_rank(matches)
        sorted_matches = self._rank_matches(ranked_matches)
        formatted_playlists = self._format_aggregated_playlist(sorted_matches)
        self._write_aggregated_playlists(formatted_playlists)

    def _group_by_genre(self, track_playlists: Collection[Any]) -> dict[GenreName, dict[str, dict[str, Any]]]:
        """Group ISRC matches across the same genre from different services."""
        candidates_by_genre: defaultdict[GenreName, defaultdict[str, defaultdict[str, Any]]] = defaultdict(
            lambda: defaultdict(lambda: defaultdict(dict))
        )
        for genre_name in GenreName:
            for service_name in TrackSourceServiceName:
                playlist = track_playlists.find_one({"genre_name": genre_name, "service_name": service_name})
                if playlist and "tracks" in playlist and playlist["tracks"]:
                    track_ranks = [TrackRank(**track) for track in playlist["tracks"]]
                    for track in track_ranks:
                        candidates_by_genre[genre_name][track.isrc]["sources"][service_name] = track.rank

        return {k: dict(v) for k, v in candidates_by_genre.items()}

    def _get_matches(
        self, candidates: dict[GenreName, dict[str, dict[str, Any]]]
    ) -> dict[GenreName, dict[str, dict[str, Any]]]:
        """Get ISRCs that come up more than once for the same genre."""
        matches: defaultdict[GenreName, defaultdict[str, dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
        for genre_name, isrcs in candidates.items():
            for isrc, isrc_data in isrcs.items():
                if len(isrc_data["sources"]) > 1:
                    matches[genre_name][isrc]["sources"] = isrc_data["sources"]
        return dict(matches)

    def _add_aggregate_rank(
        self, matches: dict[GenreName, dict[str, dict[str, Any]]]
    ) -> dict[GenreName, dict[str, dict[str, Any]]]:
        """Rank matches based on the rank of the services."""
        for _genre_name, isrcs in matches.items():
            for _isrc, isrc_data in isrcs.items():
                aggregate_service_name: TrackSourceServiceName | None = None

                for service_name in RANK_PRIORITY:
                    if service_name in isrc_data["sources"]:
                        aggregate_service_name = service_name
                        break

                if aggregate_service_name:
                    raw_aggregate_rank = isrc_data["sources"][aggregate_service_name]
                    isrc_data["raw_aggregate_rank"] = raw_aggregate_rank
                    isrc_data["aggregate_service_name"] = aggregate_service_name

        return matches

    def _rank_matches(
        self, matches: dict[GenreName, dict[str, dict[str, Any]]]
    ) -> dict[GenreName, dict[str, dict[str, Any]]]:
        for _genre_name, isrcs in matches.items():
            isrc_list = list(isrcs.values())
            isrc_list.sort(key=lambda x: x.get("raw_aggregate_rank", float("inf")))
            for rank, isrc_data in enumerate(isrc_list, start=1):
                isrc_data["rank"] = rank
        return matches

    def _format_aggregated_playlist(
        self, sorted_matches: dict[GenreName, dict[str, dict[str, Any]]]
    ) -> dict[GenreName, dict[str, Any]]:
        formatted_playlists: dict[GenreName, dict[str, Any]] = {}
        for genre_name, isrcs in sorted_matches.items():
            tracks: list[TrackRank] = []
            for isrc, isrc_data in isrcs.items():
                track = TrackRank(
                    isrc=isrc,
                    rank=isrc_data["rank"],
                    sources=isrc_data["sources"],
                    raw_aggregate_rank=isrc_data.get("raw_aggregate_rank"),
                    aggregate_service_name=isrc_data.get("aggregate_service_name"),
                )
                tracks.append(track)

            playlist = Playlist(
                service_name=PlaylistType.AGGREGATE,
                genre_name=genre_name,
                tracks=tracks,
            )
            formatted_playlists[genre_name] = playlist.model_dump()
        return formatted_playlists

    def _write_aggregated_playlists(self, formatted_playlists: dict[GenreName, dict[str, Any]]) -> None:
        logger.info("Writing aggregated playlists to MongoDB")
        for genre_name in GenreName:
            genre_name_value = genre_name.value
            if genre_name in formatted_playlists:
                playlist_dict = formatted_playlists[genre_name]
                self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION).update_one(
                    {"service_name": PlaylistType.AGGREGATE.value, "genre_name": genre_name_value},
                    {"$set": playlist_dict},
                    upsert=True,
                )
