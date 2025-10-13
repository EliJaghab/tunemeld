import time

from core.models.playlist import PlaylistModel
from core.models.track import TrackFeatureModel, TrackModel
from core.services.spotify_service import extract_spotify_track_id_from_url, get_spotify_audio_features
from core.utils.utils import get_logger
from django.core.management.base import BaseCommand

logger = get_logger(__name__)


class Command(BaseCommand):
    help = "Populate Spotify audio features for tracks on current playlists"

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=None, help="Limit number of tracks to process (for testing)")

    def handle(self, *args, **options):
        start_time = time.time()
        limit = options.get("limit")

        playlist_isrcs = set(PlaylistModel.objects.values_list("isrc", flat=True).distinct())
        logger.info(f"Found {len(playlist_isrcs)} unique tracks on current playlists")

        existing_isrcs = set(TrackFeatureModel.objects.values_list("isrc", flat=True))
        tracks_query = TrackModel.objects.filter(isrc__in=playlist_isrcs, spotify_url__isnull=False).exclude(
            isrc__in=existing_isrcs
        )
        logger.info("Processing tracks on current playlists with Spotify URLs but missing audio features")

        tracks_query = tracks_query.order_by("isrc")

        if limit:
            tracks_query = tracks_query[:limit]
            logger.info(f"Limited to {limit} tracks for testing")

        tracks_list = list(tracks_query)
        total_tracks = len(tracks_list)

        if total_tracks == 0:
            logger.info("No tracks found to process")
            return

        logger.info(f"Processing {total_tracks} tracks for audio features extraction (sequential)...")

        success_count = 0
        skipped_count = 0
        error_count = 0

        for i, track in enumerate(tracks_list, 1):
            try:
                features = self.process_track(track)
                if features:
                    success_count += 1
                else:
                    skipped_count += 1
                    logger.info(f"Skipped track {track.isrc} ({track.track_name}) - not found in ReccoBeats")
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing track {track.isrc} ({track.track_name}): {e}")

            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total_tracks} ({success_count} success, {skipped_count} skipped)")

            time.sleep(0.1)

        duration = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("Audio Features ETL Results:")
        logger.info(f"Total tracks processed: {total_tracks}")
        logger.info(f"Successful: {success_count}")
        logger.info(f"Skipped (not in ReccoBeats): {skipped_count}")
        logger.info(f"Failed (errors): {error_count}")
        logger.info(f"Duration: {duration:.1f} seconds")
        logger.info("=" * 80)

    def process_track(self, track: TrackModel) -> dict | None:
        """
        Process a single track to fetch and save audio features.

        Args:
            track: TrackModel instance

        Returns:
            Dictionary of audio features if successful, None if track not found in ReccoBeats
        """
        spotify_id = extract_spotify_track_id_from_url(track.spotify_url)
        features = get_spotify_audio_features(spotify_id)

        if not features:
            return None

        TrackFeatureModel.objects.update_or_create(
            isrc=track.isrc,
            defaults={
                "danceability": features["danceability"],
                "energy": features["energy"],
                "valence": features["valence"],
                "acousticness": features["acousticness"],
                "instrumentalness": features["instrumentalness"],
                "speechiness": features["speechiness"],
                "liveness": features["liveness"],
                "tempo": features["tempo"],
                "loudness": features["loudness"],
            },
        )

        return features
