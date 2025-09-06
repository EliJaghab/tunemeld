"""
Unit Tests for Phase 3: Normalize Raw Playlists Command

WHAT THESE TESTS COVER:
Tests the parsing of raw JSON from different music services into clean,
structured data format. Ensures each service's unique JSON structure
is correctly normalized into a standard format.

TEST CATEGORIES:
1. Service-specific JSON parsing (Spotify, Apple Music, SoundCloud)
2. Full normalization workflow (raw → structured playlist)
3. Data cleanup and error handling
4. Edge cases (empty playlists, malformed data)

MOCK DATA:
Uses realistic sample JSON responses from each service to ensure
parsing logic handles real-world data structures correctly.

KEY TESTS:
- test_parse_spotify_tracks: Validates Spotify "tracks.items" parsing
- test_parse_apple_music_tracks: Validates Apple Music "album_details" parsing
- test_parse_soundcloud_tracks: Validates SoundCloud title splitting
- test_normalize_raw_playlist_spotify: Full workflow test
- test_clear_structured_playlists: Cleanup functionality
"""

from core.management.commands.c_normalize_raw_playlists import Command as NormalizeCommand
from core.models import Genre, PlaylistTrack, RawPlaylistData, Service
from django.test import TestCase


class TestNormalizeRawPlaylistsCommand(TestCase):
    def setUp(self):
        """Set up test data."""
        self.command = NormalizeCommand()

        # Create test service and genre
        self.spotify_service = Service.objects.create(name="Spotify", display_name="Spotify")
        self.pop_genre = Genre.objects.create(name="pop", display_name="Pop")

        self.spotify_raw_data = {
            "items": [
                {
                    "track": {
                        "id": "4iV5W9uYEdYUVa79Axb7Rh",
                        "name": "Flowers",
                        "artists": [{"name": "Miley Cyrus"}],
                        "album": {
                            "name": "Endless Summer Vacation",
                            "images": [{"url": "https://example.com/cover.jpg"}],
                        },
                        "duration_ms": 200000,
                        "popularity": 85,
                        "external_ids": {"isrc": "USSM12301546"},
                        "external_urls": {"spotify": "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"},
                        "preview_url": "https://example.com/preview.mp3",
                    }
                }
            ]
        }

        self.apple_music_raw_data = {
            "album_details": {
                "0": {
                    "name": "Flowers",
                    "artist": "Miley Cyrus",
                    "album": "Endless Summer Vacation",
                    "link": "https://music.apple.com/track/123",
                }
            }
        }

        self.soundcloud_raw_data = {
            "tracks": {
                "items": [
                    {
                        "id": "123456789",
                        "title": "Miley Cyrus - Flowers",
                        "user": {"name": "Miley Cyrus"},
                        "duration": 200000,
                        "play_count": 1000000,
                        "publisher": {"isrc": "USSM12301546"},
                        "permalink": "https://soundcloud.com/track/123",
                        "stream_url": "https://example.com/stream.mp3",
                        "artworkUrl": "https://example.com/artwork.jpg",
                    }
                ]
            }
        }

    def test_parse_spotify_tracks(self):
        """Test parsing Spotify raw JSON."""
        tracks = self.command.parse_spotify_tracks(self.spotify_raw_data)

        assert len(tracks) == 1
        track = tracks[0]

        assert track["position"] == 1
        assert track["service_track_id"] == "4iV5W9uYEdYUVa79Axb7Rh"
        assert track["name"] == "Flowers"
        assert track["artist"] == "Miley Cyrus"
        assert track["album"] == "Endless Summer Vacation"
        assert track["duration_ms"] == 200000
        assert track["popularity"] == 85
        assert track["external_ids"]["isrc"] == "USSM12301546"
        assert "spotify" in track["external_urls"]
        assert track["album_cover_url"] == "https://example.com/cover.jpg"

    def test_parse_apple_music_tracks(self):
        """Test parsing Apple Music raw JSON."""
        tracks = self.command.parse_apple_music_tracks(self.apple_music_raw_data)

        assert len(tracks) == 1
        track = tracks[0]

        assert track["position"] == 1
        assert track["name"] == "Flowers"
        assert track["artist"] == "Miley Cyrus"
        assert track["album"] == "Endless Summer Vacation"
        assert track["duration_ms"] is None  # Not provided by Apple Music
        assert track["external_urls"]["apple_music"] == "https://music.apple.com/track/123"

    def test_parse_soundcloud_tracks(self):
        """Test parsing SoundCloud raw JSON."""
        tracks = self.command.parse_soundcloud_tracks(self.soundcloud_raw_data)

        assert len(tracks) == 1
        track = tracks[0]

        assert track["position"] == 1
        assert track["service_track_id"] == "123456789"
        assert track["name"] == "Flowers"
        assert track["artist"] == "Miley Cyrus"
        assert track["duration_ms"] == 200000
        assert track["popularity"] == 1000000
        assert track["external_ids"]["isrc"] == "USSM12301546"
        assert "soundcloud" in track["external_urls"]

    def test_create_playlist_tracks_spotify(self):
        """Test full creation of PlaylistTrack records from Spotify raw playlist."""
        raw_data = RawPlaylistData.objects.create(
            service=self.spotify_service,
            genre=self.pop_genre,
            playlist_url="https://open.spotify.com/playlist/123",
            playlist_name="Today's Top Hits",
            data=self.spotify_raw_data,
        )

        track_count = self.command.create_playlist_tracks(raw_data)

        assert track_count == 1

        playlist_track = PlaylistTrack.objects.get(service=self.spotify_service, genre=self.pop_genre)
        assert playlist_track.position == 1
        assert playlist_track.service_track_id == "4iV5W9uYEdYUVa79Axb7Rh"
        assert playlist_track.track_name == "Flowers"
        assert playlist_track.artist_name == "Miley Cyrus"
        assert playlist_track.album_name == "Endless Summer Vacation"
        assert playlist_track.isrc == "USSM12301546"
        assert playlist_track.spotify_url == "https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh"
        assert playlist_track.preview_url == "https://example.com/preview.mp3"
        assert playlist_track.album_cover_url == "https://example.com/cover.jpg"

    def test_clear_playlist_tracks(self):
        """Test clearing existing playlist tracks."""
        PlaylistTrack.objects.create(
            service=self.spotify_service,
            genre=self.pop_genre,
            position=1,
            track_name="Test Track",
            artist_name="Test Artist",
        )

        assert PlaylistTrack.objects.count() == 1

        self.command.clear_playlist_tracks()

        assert PlaylistTrack.objects.count() == 0

    def test_empty_tracks_handling(self):
        """Test handling of playlists with no tracks."""
        empty_data = {"items": []}
        tracks = self.command.parse_spotify_tracks(empty_data)
        assert len(tracks) == 0
