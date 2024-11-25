from playlist_etl.config import CURRENT_TIMESTAMP, TRACK_COLLECTION, TRACK_PLAYLIST_COLLECTION
from playlist_etl.helpers import get_logger
from playlist_etl.models import GenreName, HistoricalView, PlaylistType, Track
from playlist_etl.mongo_db_client import MongoDBClient
from playlist_etl.services import YouTubeService
from playlist_etl.utils import WebDriverManager

logger = get_logger(__name__)


class ViewCount:
    def __init__(
        self,
        mongo_client: MongoDBClient,
        web_driver: WebDriverManager,
        youtube_service: YouTubeService,
    ):
        self.mongo_client = mongo_client
        self.web_driver = web_driver
        self.youtube_service = youtube_service

    def update(self):
        playlists = self.mongo_client.get_collection(TRACK_PLAYLIST_COLLECTION)
        tracks = self.mongo_client.get_collection(TRACK_COLLECTION)
        updated_tracks = self._get_new_view_count_data(playlists, tracks)
        self._update_view_counts(updated_tracks)

    def _get_new_view_count_data(self, playlists, tracks):
        updated_tracks = []
        for playlist_name in PlaylistType:
            for genre_name in GenreName:

                playlist_name = playlist_name.value
                genre_name = genre_name.value

                playlist = playlists.find_one(
                    {"service_name": playlist_name, "genre_name": genre_name}
                )

                for track in playlist["tracks"]:
                    track_data = tracks.find_one({"isrc": track["isrc"]})
                    track = Track(**track_data)
                    self._update_track_view_counts(track)
                    updated_tracks.append(track)

        return updated_tracks

    def _update_track_view_counts(self, track: Track):
        self._update_spotify_view_count(track)
        self._update_youtube_view_count(track)

    def _update_spotify_view_count(self, track: Track) -> bool:
        self._update_spotify_start_view_count(track)
        self._update_spotify_current_view_count(track)
        self._update_spotify_historical_view_count(track)

    def _update_spotify_start_view_count(self, track: Track) -> bool:
        if track.spotify_view.start_view.timestamp is not None:
            return

        track.spotify_view.start_view.view_count = self.web_driver.get_spotify_track_view_count(
            track.isrc
        )
        track.spotify_view.start_view.timestamp = CURRENT_TIMESTAMP

    def _update_spotify_current_view_count(self, track: Track) -> None:
        track.spotify_view.current_view.view_count = self.web_driver.get_spotify_track_view_count(
            track.isrc
        )
        track.spotify_view.current_view.timestamp = CURRENT_TIMESTAMP

    def _update_spotify_historical_view_count(self, track: Track) -> bool:
        historical_view = HistoricalView()
        historical_view.total_view_count = track.spotify_view.current_view.view_count
        delta_view_count = self._get_delta_view_count(
            track.spotify_view.historical_view, track.spotify_view.current_view.view_count
        )
        historical_view.delta_view_count = delta_view_count
        historical_view.timestamp = CURRENT_TIMESTAMP
        track.spotify_view.historical_view.append(historical_view)

    def _update_youtube_view_count(self, track: Track) -> bool:
        if track.youtube_view.start_view.timestamp is not None:
            return

        track.youtube_view.start_view.view_count = (
            self.youtube_service.get_youtube_track_view_count(track.youtube_url)
        )
        track.youtube_view.start_view.timestamp = CURRENT_TIMESTAMP

    def _update_youtube_current_view_count(self, track: Track) -> None:
        track.youtube_view.current_view.view_count = (
            self.youtube_service.get_youtube_track_view_count(track.youtube_url)
        )
        track.youtube_view.current_view.timestamp = CURRENT_TIMESTAMP

    def _update_youtube_historical_view_count(self, track: Track) -> bool:
        historical_view = HistoricalView()
        historical_view.total_view_count = track.youtube_view.current_view.view_count
        delta_view_count = self._get_delta_view_count(
            track.youtube_view.historical_view, track.youtube_view.current_view.view_count
        )
        historical_view.delta_view_count = delta_view_count
        historical_view.timestamp = CURRENT_TIMESTAMP
        track.youtube_view.historical_view.append(historical_view)

    def _get_delta_view_count(
        self, historical_views: list[HistoricalView], current_view_count: int
    ) -> int:
        if not historical_views:
            return 0
        return current_view_count - historical_views[-1].total_view_count

    def _update_view_counts(self, tracks):
        for track in tracks:
            self.mongo_client.update_track(track)
