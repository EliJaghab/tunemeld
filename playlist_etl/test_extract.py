import unittest
from unittest.mock import Mock, patch

from extract import SpotifyFetcher
from transform_playlist_metadata import (
    transform_creator,
    transform_featured_artist,
    transform_playlist_name,
    transform_playlist_tagline,
    transform_spotify_playlist_metadata,
)


class TestSpotifyExtraction(unittest.TestCase):
    """Test Spotify metadata extraction and transformation"""

    def setUp(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_client.api_key = "test_api_key"
        self.service_name = "Spotify"
        self.genre = "pop"

        # Mock HTML response for Today's Top Hits playlist (matches real Spotify structure)
        self.mock_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="Today's Top Hits" />
            <meta property="og:description" content="Playlist · Spotify · 50 items · 35.1M saves" />
            <meta property="og:image" content="https://i.scdn.co/image/ab67706f000000025ef8ff921561760fb462f239" />
            <meta property="music:creator" content="https://open.spotify.com/user/spotify" />
            <title>Today's Top Hits | Spotify Playlist</title>
        </head>
        <body>
            <span data-encore-id="text" variant="bodySmall"
                  class="encore-text-body-small encore-internal-color-text-subdued">
                The hottest 50. Cover: Benson Boone
            </span>
            <span class="e-9960-text encore-text-body-small">35,143,543 saves</span>
        </body>
        </html>
        """

        # Mock config matching the actual SERVICE_CONFIGS structure
        self.mock_config = {
            "base_url": "https://spotify-scraper.p.rapidapi.com/v1/playlist/contents",
            "host": "spotify-scraper.p.rapidapi.com",
            "param_key": "playlistId",
            "playlist_base_url": "https://open.spotify.com/playlist/",
            "links": {"pop": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M"},
        }

    @patch("extract.requests.get")
    @patch("extract.SERVICE_CONFIGS")
    def test_spotify_metadata_extraction_with_cover_artist(self, mock_configs, mock_get):
        """Test extraction when playlist has a cover artist"""
        # Setup mocks
        mock_configs.__getitem__.return_value = self.mock_config
        mock_response = Mock()
        mock_response.text = self.mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Create fetcher
        fetcher = SpotifyFetcher(self.mock_client, self.service_name, self.genre)
        fetcher.set_playlist_details()

        # Verify extracted metadata
        self.assertEqual(fetcher.playlist_name, "Today's Top Hits")
        self.assertEqual(fetcher.playlist_tagline, "The hottest 50.")
        self.assertEqual(fetcher.playlist_featured_artist, "Benson Boone")
        self.assertEqual(fetcher.playlist_saves_count, "35.1M")  # Enhanced parser returns formatted version
        self.assertEqual(fetcher.playlist_track_count, 50)
        self.assertEqual(fetcher.playlist_cover_url, "https://i.scdn.co/image/ab67706f000000025ef8ff921561760fb462f239")
        self.assertEqual(fetcher.playlist_creator, "spotify")
        self.assertEqual(fetcher.playlist_cover_description_text, "The hottest 50.")

    @patch("extract.requests.get")
    @patch("extract.SERVICE_CONFIGS")
    def test_spotify_metadata_extraction_without_cover_artist(self, mock_configs, mock_get):
        """Test extraction when playlist doesn't have a cover artist"""
        # Mock HTML without "Cover:" text (matches real Spotify structure)
        mock_html_no_cover = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="Dance Hits" />
            <meta property="og:description" content="Playlist · Spotify · 75 items · 5.8M saves" />
            <meta property="og:image" content="https://example.com/image.jpg" />
        </head>
        <body>
            <span data-encore-id="text" variant="bodySmall"
                  class="encore-text-body-small encore-internal-color-text-subdued">
                The world's biggest dance & electronic hits.
            </span>
            <span class="e-9960-text encore-text-body-small">5,758,625 saves</span>
        </body>
        </html>
        """

        mock_configs.__getitem__.return_value = self.mock_config
        mock_response = Mock()
        mock_response.text = mock_html_no_cover
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = SpotifyFetcher(self.mock_client, self.service_name, self.genre)
        fetcher.set_playlist_details()

        self.assertEqual(fetcher.playlist_name, "Dance Hits")
        self.assertEqual(fetcher.playlist_tagline, "The world's biggest dance & electronic hits.")
        self.assertIsNone(fetcher.playlist_featured_artist)
        self.assertEqual(fetcher.playlist_saves_count, "5.8M")  # Enhanced parser returns formatted version
        self.assertEqual(fetcher.playlist_track_count, 75)

    @patch("extract.requests.get")
    @patch("extract.SERVICE_CONFIGS")
    def test_spotify_metadata_extraction_fallback(self, mock_configs, mock_get):
        """Test extraction with fallback when main elements are missing"""
        # Minimal HTML (matches real Spotify structure)
        mock_html_minimal = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta property="og:title" content="Rock Classics" />
            <meta property="og:description" content="Playlist · Spotify · 100 items · 2.5M saves" />
        </head>
        <body>
            <span class="encore-text-body-small encore-internal-color-text-subdued">
                Classic rock anthems and deep cuts
            </span>
        </body>
        </html>
        """

        mock_configs.__getitem__.return_value = self.mock_config
        mock_response = Mock()
        mock_response.text = mock_html_minimal
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        fetcher = SpotifyFetcher(self.mock_client, self.service_name, self.genre)
        fetcher.set_playlist_details()

        self.assertEqual(fetcher.playlist_name, "Rock Classics")
        self.assertEqual(fetcher.playlist_cover_description_text, "Classic rock anthems and deep cuts")
        self.assertEqual(fetcher.playlist_tagline, "Classic rock anthems and deep cuts")
        self.assertIsNone(fetcher.playlist_featured_artist)
        self.assertEqual(fetcher.playlist_saves_count, "2.5M")  # Enhanced parser extracts from og:description
        self.assertEqual(fetcher.playlist_track_count, 100)
        self.assertEqual(fetcher.playlist_creator, "spotify")  # Default value

    @patch("extract.requests.get")
    @patch("extract.SERVICE_CONFIGS")
    def test_document_creation_with_enhanced_fields(self, mock_configs, mock_get):
        """Test that document includes all enhanced fields"""
        from extract import run_extraction

        # Setup mocks
        mock_configs.__getitem__.return_value = self.mock_config
        mock_configs.items.return_value = [("Spotify", self.mock_config)]

        mock_response = Mock()
        mock_response.text = self.mock_html
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response

        # Mock RapidAPI response
        with patch("extract.get_json_response") as mock_api:
            mock_api.return_value = {"tracks": []}

            # Mock MongoDB
            mock_mongo_client = Mock()

            with patch("extract.insert_or_update_data_to_mongo") as mock_insert:
                with patch("extract.DEBUG_MODE", False):
                    run_extraction(mock_mongo_client, self.mock_client, "Spotify", "pop")

                # Verify document structure
                mock_insert.assert_called_once()
                args = mock_insert.call_args[0]
                document = args[2]

                # Check all fields are present
                self.assertEqual(document["service_name"], "Spotify")
                self.assertEqual(document["genre_name"], "pop")
                self.assertEqual(document["playlist_name"], "Today's Top Hits")
                self.assertEqual(document["playlist_tagline"], "The hottest 50.")
                self.assertEqual(document["playlist_featured_artist"], "Benson Boone")
                self.assertEqual(document["playlist_saves_count"], "35.1M")  # Enhanced parser returns formatted
                self.assertEqual(document["playlist_track_count"], 50)
                self.assertEqual(document["playlist_creator"], "spotify")  # Default value, not from meta tag
                self.assertIn("playlist_cover_url", document)
                self.assertIn("data_json", document)


class TestSpotifyMetadataTransformation(unittest.TestCase):
    """Test Spotify metadata transformation to clean strings"""

    def test_transform_playlist_name(self):
        """Test playlist name cleaning"""
        self.assertEqual(transform_playlist_name("Today's Top Hits"), "Today's Top Hits")
        self.assertEqual(transform_playlist_name("Today's Top Hits | Spotify Playlist"), "Today's Top Hits")
        self.assertEqual(transform_playlist_name("Unknown"), "Untitled Playlist")

    def test_transform_playlist_tagline(self):
        """Test tagline cleaning and formatting"""
        self.assertEqual(transform_playlist_tagline("The hottest 50"), "The hottest 50.")
        self.assertEqual(transform_playlist_tagline("The hottest 50 Spotify"), "The hottest 50.")
        self.assertEqual(transform_playlist_tagline("The hottest 50 35,143,543 saves"), "The hottest 50.")
        self.assertIsNone(transform_playlist_tagline(None))

    def test_transform_featured_artist(self):
        """Test featured artist name cleaning"""
        self.assertEqual(transform_featured_artist("Benson Boone"), "Benson Boone")
        self.assertEqual(transform_featured_artist("Benson Boone 35,143,543 saves"), "Benson Boone")
        self.assertIsNone(transform_featured_artist(None))

    def test_transform_creator(self):
        """Test creator formatting"""
        self.assertEqual(transform_creator("https://open.spotify.com/user/spotify"), "Spotify")
        self.assertEqual(transform_creator("some_user"), "some_user")
        self.assertEqual(transform_creator(None), "Spotify")

    def test_full_metadata_transformation(self):
        """Test complete metadata transformation"""
        raw_metadata = {
            "service_name": "Spotify",
            "genre_name": "pop",
            "playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "playlist_cover_url": "https://i.scdn.co/image/example.jpg",
            "playlist_name": "Today's Top Hits | Spotify Playlist",
            "playlist_tagline": "The hottest 50",
            "playlist_featured_artist": "Benson Boone",
            "playlist_creator": "https://open.spotify.com/user/spotify",
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Check description text combines tagline + Cover: artist
        expected_description = "The hottest 50. Cover: Benson Boone"
        self.assertEqual(result["playlist_cover_description_text"], expected_description)
        self.assertEqual(result["playlist_featured_artist"], "Benson Boone")

        # Check preserved fields
        self.assertEqual(result["service_name"], "Spotify")
        self.assertEqual(result["genre_name"], "pop")
        self.assertEqual(result["playlist_url"], raw_metadata["playlist_url"])
        self.assertIn("raw_metadata", result)


if __name__ == "__main__":
    unittest.main()
