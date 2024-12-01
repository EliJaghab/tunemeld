from playlist_etl.config import CURRENT_TIMESTAMP, TRACK_COLLECTION, TRACK_PLAYLIST_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.models import GenreName, HistoricalView, PlaylistType, Track
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import SpotifyService, YouTubeService
from playlist_etl.utils import WebDriverManager

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
        logger.info(
            f"Found updates for {len(updated_tracks)} out of {collection_count} total tracks"
        )
        self._save_view_counts(updated_tracks)

    def _update_tracks(self, playlists, tracks):
        updated_tracks = []
        for playlist_name in PlaylistType:
            for genre_name in GenreName:

                playlist = playlists.find_one(
                    {"service_name": playlist_name, "genre_name": genre_name}
                )

                for track in playlist["tracks"]:
                    track_data = tracks.find_one({"isrc": track["isrc"]})
                    track = Track(**track_data)

                    if self._update_track(track):
                        logger.info(f"Updated view counts for {track.isrc}")
                        updated_tracks.append(track)
                    else:
                        logger.info(f"No updates for {track.isrc}")

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

    def _save_view_counts(self, tracks):
        for track in tracks:
            self.mongo_client.update_track(track)
