from datetime import datetime, timedelta

from pymongo.collection import Collection

from playlist_etl.config import TRACK_COLLECTION, TRACK_PLAYLIST_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.models import GenreName, PlaylistType, Track
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import SpotifyService, YouTubeService

logger = get_logger(__name__)


class ViewCountTrackProcessor:
    def __init__(
        self,
        mongo_client: MongoDBClient,
        spotify_service: SpotifyService,
        youtube_service: YouTubeService,
    ):
        self.mongo_client = mongo_client
        self.spotify_service = spotify_service
        self.youtube_service = youtube_service

    def update_view_counts(self):
        playlists = self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION)
        tracks_collection = self.mongo_client.get_collection(TRACK_COLLECTION)
        updated_tracks = self._update_tracks(playlists, tracks_collection)
        collection_count = self.mongo_client.get_collection_count(tracks_collection)
        logger.info(f"Found updates for {len(updated_tracks)} out of {collection_count} total tracks")
        self._save_view_counts(updated_tracks)

    def _update_tracks(self, playlists: Collection, tracks: Collection):
        updated_tracks = []
        seen_isrc = set()
        total_tracks = self.mongo_client.get_collection_count(tracks)
        processed_tracks = 0
        skipped_tracks = 0

        # Skip tracks updated within the last 24 hours to reduce API calls
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for playlist_name in PlaylistType:
            for genre_name in GenreName:
                playlist = playlists.find_one({"service_name": playlist_name, "genre_name": genre_name})

                if not playlist:
                    continue

                for track in playlist["tracks"]:
                    track_data = tracks.find_one({"isrc": track["isrc"]})
                    if not track_data:
                        continue

                    track = Track(**track_data)

                    if track.isrc in seen_isrc:
                        continue
                    seen_isrc.add(track.isrc)

                    # Skip tracks updated recently to reduce API load
                    if self._was_recently_updated(track, cutoff_time):
                        skipped_tracks += 1
                        logger.info(f"Skipping recently updated track {track.isrc}")
                        continue

                    if self._update_track(track):
                        logger.info(f"Updated view counts for {track.isrc}")
                        updated_tracks.append(track)
                    else:
                        logger.info(f"No updates for {track.isrc}")

                    processed_tracks += 1
                    completion_percentage = (processed_tracks / total_tracks) * 100
                    logger.info(f"Processing: {completion_percentage:.2f}% complete (skipped {skipped_tracks} recent)")

        logger.info(f"Skipped {skipped_tracks} recently updated tracks to avoid rate limits")
        return updated_tracks

    def _update_track(self, track: Track) -> bool:
        spotify_updated = self._update_spotify_count(track)
        youtube_updated = self._update_youtube_count(track)
        return spotify_updated or youtube_updated

    def _update_spotify_count(self, track: Track) -> bool:
        if not self.spotify_service.set_track_url(track):
            return False

        return self.spotify_service.update_view_count(track)

    def _update_youtube_count(self, track: Track) -> bool:
        if not self.youtube_service.set_track_url(track):
            return False
        return self.youtube_service.update_view_count(track)

    def _was_recently_updated(self, track: Track, cutoff_time: datetime) -> bool:
        """Check if track view counts were updated recently to avoid redundant API calls."""
        if (
            hasattr(track, "spotify_view")
            and track.spotify_view
            and hasattr(track.spotify_view, "current_view")
            and track.spotify_view.current_view
            and hasattr(track.spotify_view.current_view, "timestamp")
        ):
            return track.spotify_view.current_view.timestamp > cutoff_time

        if (
            hasattr(track, "youtube_view")
            and track.youtube_view
            and hasattr(track.youtube_view, "current_view")
            and track.youtube_view.current_view
            and hasattr(track.youtube_view.current_view, "timestamp")
        ):
            return track.youtube_view.current_view.timestamp > cutoff_time

        return False

    def _save_view_counts(self, tracks):
        for track in tracks:
            self.mongo_client.update_track(track)
