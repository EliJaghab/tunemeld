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
                "service_name": TrackSourceServiceName.AGGREGATE.value,
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
                {"service_name": TrackSourceServiceName.AGGREGATE.value, "genre_name": genre_name},
                {"$set": playlist},
                upsert=True,
            )