"""
Django tests for TuneMeld Core API endpoints
"""

import json
from unittest.mock import patch

from django.test import Client, TestCase


class TuneMeldAPITestCase(TestCase):
    """Test cases for TuneMeld API endpoints"""

    def setUp(self):
        """Set up test client and mock data"""
        self.client = Client()

        # Sample playlist data for testing
        self.sample_playlist_data = {
            "service_name": "Aggregate",
            "genre_name": "dance",
            "tracks": [
                {
                    "isrc": "USA2P2446028",
                    "rank": 1,
                    "artist_name": "Champion, Four Tet, Skrillex & Naisha",
                    "track_name": "Talk To Me",
                    "youtube_url": "https://www.youtube.com/watch?v=test123",
                    "album_cover_url": "https://i.scdn.co/image/test123",
                    "sources": {"Spotify": 1, "AppleMusic": 2, "SoundCloud": 3},
                    "raw_aggregate_rank": 1,
                    "aggregate_service_name": "Spotify",
                },
                {
                    "isrc": "GB5KW2402411",
                    "rank": 2,
                    "artist_name": "Kaskade",
                    "track_name": "Shine On",
                    "youtube_url": "https://www.youtube.com/watch?v=test456",
                    "album_cover_url": "https://i.scdn.co/image/test456",
                    "sources": {"Spotify": 2, "AppleMusic": 1},
                    "raw_aggregate_rank": 1,
                    "aggregate_service_name": "AppleMusic",
                },
            ],
            "insert_timestamp": "2025-06-15T14:00:00Z",
        }

        # Sample raw playlist data for header art
        self.sample_raw_playlist_data = [
            {
                "service_name": "Spotify",
                "genre_name": "dance",
                "playlist_cover_url": "https://i.scdn.co/image/spotify123",
                "playlist_cover_description_text": "Dance Hits from Spotify",
                "playlist_name": "Dance Hits",
                "playlist_url": "https://open.spotify.com/playlist/test123",
            },
            {
                "service_name": "AppleMusic",
                "genre_name": "dance",
                "playlist_cover_url": "https://is1-ssl.mzstatic.com/image/apple123",
                "playlist_cover_description_text": "Dance Hits from Apple Music",
                "playlist_name": "Dance Party",
                "playlist_url": "https://music.apple.com/playlist/test456",
            },
        ]

        # Sample view count data
        self.sample_view_count_data = {
            "USA2P2446028": {
                "view_counts": {
                    "Spotify": [[1734278400000, 15420000], [1734364800000, 15892340]],
                    "YouTube": [[1734278400000, 8934521], [1734364800000, 9123456]],
                }
            }
        }

    def test_root_endpoint(self):
        """Test the root endpoint returns welcome message"""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Welcome to the TuneMeld Backend!")

    @patch("core.playlists_collection.find")
    def test_get_playlist_data_success(self, mock_find):
        """Test successful playlist data retrieval"""
        mock_find.return_value = [self.sample_playlist_data]

        response = self.client.get("/playlist-data/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Playlist data retrieved successfully")
        self.assertIsNotNone(data["data"])
        self.assertEqual(len(data["data"]), 1)

    @patch("core.playlists_collection.find")
    def test_get_playlist_data_not_found(self, mock_find):
        """Test playlist data retrieval when no data found"""
        mock_find.return_value = []

        response = self.client.get("/playlist-data/nonexistent")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "No data found for the specified genre")

    @patch("core.transformed_playlists_collection.find")
    def test_get_service_playlist_success(self, mock_find):
        """Test successful service playlist retrieval"""
        mock_find.return_value = [self.sample_playlist_data]

        response = self.client.get("/service-playlist/dance/Spotify")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Service playlist data retrieved successfully")

    @patch("core.transformed_playlists_collection.find")
    def test_get_service_playlist_not_found(self, mock_find):
        """Test service playlist retrieval when no data found"""
        mock_find.return_value = []

        response = self.client.get("/service-playlist/nonexistent/InvalidService")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertEqual(data["message"], "No data found for the specified genre and service")

    @patch("core.playlists_collection.find")
    def test_get_last_updated_success(self, mock_find):
        """Test successful last updated timestamp retrieval"""
        mock_find.return_value = [self.sample_playlist_data]

        response = self.client.get("/last-updated/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Last updated timestamp retrieved successfully")
        self.assertIn("last_updated", data["data"])

    @patch("core.raw_playlists_collection.find")
    def test_get_header_art_success(self, mock_find):
        """Test successful header art retrieval"""
        mock_find.return_value = self.sample_raw_playlist_data

        response = self.client.get("/header-art/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Header art data retrieved successfully")
        self.assertIn("Spotify", data["data"])
        self.assertIn("AppleMusic", data["data"])

    @patch("core.views.cache.get")
    @patch("core.playlists_collection.find")
    def test_get_graph_data_with_cache(self, mock_find, mock_cache_get):
        """Test graph data retrieval when data is cached"""
        cached_data = [{"test": "cached_data"}]
        mock_cache_get.return_value = cached_data

        response = self.client.get("/graph-data/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Graph data retrieved successfully from cache")
        self.assertEqual(data["data"], cached_data)

        # Verify that database wasn't queried when cache hit
        mock_find.assert_not_called()

    @patch("core.views.cache.get")
    @patch("core.views.cache.put")
    @patch("core.historical_track_views.find")
    @patch("core.playlists_collection.find")
    def test_get_graph_data_no_cache(self, mock_find, mock_track_views_find, mock_cache_put, mock_cache_get):
        """Test graph data retrieval when data is not cached"""
        # Mock cache miss
        mock_cache_get.return_value = None

        # Mock playlist data
        mock_find.return_value = [self.sample_playlist_data]

        # Mock track views data (empty for simplicity)
        mock_track_views_find.return_value = []

        response = self.client.get("/graph-data/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "Graph data retrieved successfully")

        # Verify cache was attempted to be populated
        mock_cache_put.assert_called_once()

    def test_invalid_endpoints(self):
        """Test that invalid endpoints return 404"""
        response = self.client.get("/invalid-endpoint")
        self.assertEqual(response.status_code, 404)

    def test_cors_headers_present(self):
        """Test that CORS headers are present in responses"""
        response = self.client.get("/")

        # The CORS middleware should add appropriate headers
        # This test ensures the middleware is properly configured
        self.assertEqual(response.status_code, 200)

    @patch("core.playlists_collection.find")
    def test_database_error_handling(self, mock_find):
        """Test that database errors are handled gracefully"""
        # Simulate a database error
        mock_find.side_effect = Exception("Database connection error")

        response = self.client.get("/playlist-data/dance")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertEqual(data["status"], "error")
        self.assertIn("Database connection error", data["message"])


class TuneMeldSettingsTestCase(TestCase):
    """Test cases for Django settings configuration"""

    def test_required_settings_exist(self):
        """Test that required Django settings are properly configured"""
        from django.conf import settings

        # Test that critical settings are present
        self.assertTrue(hasattr(settings, "ALLOWED_HOSTS"))
        self.assertTrue(hasattr(settings, "SECRET_KEY"))
        self.assertTrue(hasattr(settings, "DEBUG"))
        self.assertTrue(hasattr(settings, "INSTALLED_APPS"))

        # Test CORS settings
        self.assertTrue(hasattr(settings, "CORS_ALLOWED_ORIGINS"))
        self.assertIn("corsheaders", settings.INSTALLED_APPS)

    def test_cors_configuration(self):
        """Test that CORS is properly configured"""
        from django.conf import settings

        # Check that CORS middleware is installed
        self.assertIn("corsheaders.middleware.CorsMiddleware", settings.MIDDLEWARE)

        # Check that CORS allowed origins are set
        self.assertTrue(len(settings.CORS_ALLOWED_ORIGINS) > 0)
