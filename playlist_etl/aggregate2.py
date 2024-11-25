from collections import defaultdict

from playlist_etl.config import RANK_PRIORITY, TRACK_PLAYLIST_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.models import GenreName, Playlist, PlaylistType, TrackRank, TrackSourceServiceName
from playlist_etl.mongo_db_client import MongoDBClient

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
        candidates_by_genre = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for genre_name in GenreName:
            for service_name in TrackSourceServiceName:
                playlist = track_playlists.find_one(
                    {"genre_name": genre_name, "service_name": service_name}
                )
                track_ranks = [TrackRank(**track) for track in playlist["tracks"]]
                for track in track_ranks:
                    candidates_by_genre[genre_name][track.isrc]["sources"][
                        service_name
                    ] = track.rank

        return candidates_by_genre

    def _get_matches(self, candidates: dict) -> dict:
        """Get ISRCs that come up more than once for the same genre."""
        matches = defaultdict(lambda: defaultdict(dict))
        for genre_name, isrcs in candidates.items():
            for isrc, isrc_data in isrcs.items():
                if len(isrc_data["sources"]) > 1:
                    matches[genre_name][isrc]["sources"] = isrc_data["sources"]
        return matches

    def _add_aggregate_rank(self, matches: dict) -> dict:
        """Rank matches based on the rank of the services."""
        for genre_name, isrcs in matches.items():
            for isrc, isrc_data in isrcs.items():
                aggregate_service_name = None

                for service_name in RANK_PRIORITY:
                    if service_name in isrc_data["sources"]:
                        aggregate_service_name = service_name
                        break

                raw_aggregate_rank = isrc_data["sources"][aggregate_service_name]
                isrc_data["raw_aggregate_rank"] = raw_aggregate_rank
                isrc_data["aggregate_service_name"] = aggregate_service_name

        return matches

    def _rank_matches(self, matches: dict) -> dict:
        for genre_name, isrcs in matches.items():
            isrc_list = list(isrcs.values())
            isrc_list.sort(key=lambda x: x["raw_aggregate_rank"])
            for rank, isrc_data in enumerate(isrc_list, start=1):
                isrc_data["rank"] = rank
        return matches

    def _format_aggregated_playlist(self, sorted_matches: dict) -> list[dict]:
        formatted_playlists = {}
        for genre_name, isrcs in sorted_matches.items():
            tracks = []
            for isrc, isrc_data in isrcs.items():
                track = TrackRank(
                    isrc=isrc,
                    rank=isrc_data["rank"],
                    sources=isrc_data["sources"],
                    raw_aggregate_rank=isrc_data["raw_aggregate_rank"],
                    aggregate_service_name=isrc_data["aggregate_service_name"],
                )
                tracks.append(track.model_dump())

            playlist = Playlist(
                service_name=PlaylistType.AGGREGATE,
                genre_name=genre_name,
                tracks=tracks,
            )
            formatted_playlists[genre_name] = playlist.model_dump()
        return formatted_playlists

    def _write_aggregated_playlists(self, formatted_playlists: dict) -> None:
        logger.info("Writing aggregated playlists to MongoDB")
        for genre_name in GenreName:
            genre_name = genre_name.value
            playlist_dict = formatted_playlists[genre_name]
            self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION).update_one(
                {"service_name": PlaylistType.AGGREGATE.value, "genre_name": genre_name},
                {"$set": playlist_dict},
                upsert=True,
            )
