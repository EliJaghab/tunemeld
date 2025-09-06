"""
Unit Tests for Phase 4: Hydrate Tracks Command

WHAT THESE TESTS COVER:
Tests ISRC resolution logic and canonical Track creation from structured
playlist data. Validates that tracks are properly deduplicated by ISRC
and service-specific metadata is correctly linked.

TEST CATEGORIES:
1. ISRC resolution for different services (Spotify, SoundCloud, Apple Music)
2. Track deduplication logic (same ISRC = same Track)
3. TrackData and TrackPlaylist creation
4. Error handling (missing ISRCs, malformed data)
5. Data cleanup functionality

KEY DEDUPLICATION TEST:
test_track_deduplication_by_isrc verifies that when the same song appears
on multiple services with the same ISRC, only one canonical Track is created
while preserving service-specific metadata in separate TrackData records.

ISRC RESOLUTION TESTS:
- test_resolve_isrc_spotify: Direct ISRC extraction from external_ids
- test_resolve_isrc_soundcloud: Direct ISRC from publisher field
- test_resolve_isrc_apple_music: Spotify API lookup (placeholder for now)
- test_resolve_isrc_missing: Graceful handling of missing ISRCs

MOCK DATA:
Uses structured track data (output from Phase 3) with realistic ISRC values
to test the hydration process end-to-end.
"""

from unittest.mock import Mock, patch

from core.management.commands.d_hydrate_tracks import Command as HydrateCommand
from core.models import Genre, PlaylistTrack, Service, Track, TrackData
from django.test import TestCase


class TestHydrateTracksCommand(TestCase):
    @patch("core.management.commands.d_hydrate_tracks.WebDriverManager")
    @patch("core.management.commands.d_hydrate_tracks.CacheManager")
    @patch("core.management.commands.d_hydrate_tracks.MongoDBClient")
    @patch("core.management.commands.d_hydrate_tracks.SpotifyService")
    @patch("core.management.commands.d_hydrate_tracks.os.getenv")
    def setUp(self, mock_getenv, mock_spotify_service, mock_mongo_client, mock_cache_manager, mock_webdriver_manager):
        """Set up test data."""
        # Mock environment variables for Spotify credentials
        mock_getenv.side_effect = lambda key: {
            "SPOTIFY_CLIENT_ID": "test_client_id",
            "SPOTIFY_CLIENT_SECRET": "test_client_secret",
        }.get(key)

        # Mock the Spotify service
        self.mock_spotify_service = Mock()
        mock_spotify_service.return_value = self.mock_spotify_service

        self.command = HydrateCommand()

        self.spotify_service = Service.objects.create(name="Spotify", display_name="Spotify")
        self.soundcloud_service = Service.objects.create(name="SoundCloud", display_name="SoundCloud")
        self.apple_music_service = Service.objects.create(name="AppleMusic", display_name="Apple Music")
        self.pop_genre = Genre.objects.create(name="pop", display_name="Pop")

        self.spotify_playlist_track = PlaylistTrack.objects.create(
            service=self.spotify_service,
            genre=self.pop_genre,
            position=1,
            service_track_id="4iV5W9uYEdYUVa79Axb7Rh",
            track_name="Flowers",
            artist_name="Miley Cyrus",
            album_name="Endless Summer Vacation",
            isrc="USSM12301546",
            spotify_url="https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh",
            preview_url="https://example.com/preview.mp3",
            album_cover_url="https://example.com/cover.jpg",
        )

        self.soundcloud_playlist_track = PlaylistTrack.objects.create(
            service=self.soundcloud_service,
            genre=self.pop_genre,
            position=1,
            service_track_id="123456789",
            track_name="Flowers",
            artist_name="Miley Cyrus",
            isrc="USSM12301546",  # Same ISRC as Spotify
            soundcloud_url="https://soundcloud.com/track/123",
            preview_url="https://example.com/stream.mp3",
            album_cover_url="https://example.com/artwork.jpg",
        )

    def test_resolve_isrc_spotify(self):
        """Test ISRC resolution for Spotify tracks."""
        isrc = self.command.resolve_isrc_from_playlist_track(self.spotify_playlist_track)

        assert isrc == "USSM12301546"

    def test_resolve_isrc_soundcloud(self):
        """Test ISRC resolution for SoundCloud tracks."""
        isrc = self.command.resolve_isrc_from_playlist_track(self.soundcloud_playlist_track)

        assert isrc == "USSM12301546"

    def test_resolve_isrc_apple_music(self):
        """Test ISRC resolution for Apple Music tracks via Spotify lookup."""
        apple_music_track = PlaylistTrack.objects.create(
            service=self.apple_music_service,
            genre=self.pop_genre,
            position=1,
            track_name="Flowers",
            artist_name="Miley Cyrus",
            apple_music_url="https://music.apple.com/track/123",
        )

        # Mock Spotify service to return an ISRC
        self.mock_spotify_service.get_isrc.return_value = "USSM12301546"

        isrc = self.command.resolve_isrc_from_playlist_track(apple_music_track)

        # Should return ISRC from Spotify lookup
        assert isrc == "USSM12301546"
        self.mock_spotify_service.get_isrc.assert_called_once_with("Flowers", "Miley Cyrus")

    def test_resolve_isrc_missing(self):
        """Test ISRC resolution when no ISRC is available."""
        track_without_isrc = PlaylistTrack.objects.create(
            service=self.spotify_service,
            genre=self.pop_genre,
            position=2,
            track_name="Unknown Song",
            artist_name="Unknown Artist",
        )

        isrc = self.command.resolve_isrc_from_playlist_track(track_without_isrc)

        assert isrc is None

    def test_track_deduplication_by_isrc(self):
        """Test that tracks with same ISRC are deduplicated."""
        self.command.handle()

        # Should only create one track for the same ISRC
        assert Track.objects.count() == 1

        # Should create two TrackData records (one for each service)
        assert TrackData.objects.count() == 2

        track = Track.objects.first()
        assert track.isrc == "USSM12301546"
        assert track.track_name == "Flowers"
        assert track.artist_name == "Miley Cyrus"

        spotify_data = TrackData.objects.filter(service=self.spotify_service).first()
        soundcloud_data = TrackData.objects.filter(service=self.soundcloud_service).first()

        assert spotify_data.track == track
        assert soundcloud_data.track == track
        assert spotify_data.service_track_id == "4iV5W9uYEdYUVa79Axb7Rh"
        assert soundcloud_data.service_track_id == "123456789"

    def test_clear_track_data(self):
        """Test clearing existing track data."""
        track = Track.objects.create(track_name="Test Track", artist_name="Test Artist", isrc="TEST123456789")
        TrackData.objects.create(track=track, service=self.spotify_service, service_track_id="test123")

        assert Track.objects.count() == 1
        assert TrackData.objects.count() == 1

        self.command.clear_track_data()

        assert Track.objects.count() == 0
        assert TrackData.objects.count() == 0

    def test_handle_no_playlist_tracks(self):
        """Test handling when no playlist tracks exist."""
        PlaylistTrack.objects.all().delete()

        self.command.handle()

    def test_get_service_url(self):
        """Test getting the appropriate service URL from PlaylistTrack."""
        spotify_url = self.command.get_service_url(self.spotify_playlist_track)
        assert spotify_url == "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"

        soundcloud_url = self.command.get_service_url(self.soundcloud_playlist_track)
        assert soundcloud_url == "https://soundcloud.com/track/123"

        track_no_url = PlaylistTrack.objects.create(
            service=self.spotify_service,
            genre=self.pop_genre,
            position=3,
            track_name="No URL Track",
            artist_name="Test Artist",
        )
        empty_url = self.command.get_service_url(track_no_url)
        assert empty_url == ""
