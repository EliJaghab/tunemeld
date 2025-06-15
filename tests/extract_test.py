"""
Comprehensive tests for extract.py
Tests playlist extraction from external APIs with realistic service configurations
"""

import json
from unittest.mock import Mock, patch

import pytest
import requests

from playlist_etl.extract import (
    PLAYLIST_GENRES,
    SERVICE_CONFIGS,
    AppleMusicFetcher,
    Extractor,
    RapidAPIClient,
    SoundCloudFetcher,
    SpotifyFetcher,
    get_json_response,
    run_extraction,
)


class TestRapidAPIClient:
    """Test suite for RapidAPIClient class"""

    @patch.dict("os.environ", {"X_RAPIDAPI_KEY": "test_api_key_123"})
    def test_init_with_api_key(self):
        """Test RapidAPIClient initialization with valid API key"""
        client = RapidAPIClient()
        assert client.api_key == "test_api_key_123"

    @patch.dict("os.environ", {}, clear=True)
    def test_init_without_api_key(self):
        """Test RapidAPIClient initialization without API key raises exception"""
        with pytest.raises(Exception, match="Failed to set API Key"):
            RapidAPIClient()

    @patch.dict("os.environ", {"X_RAPIDAPI_KEY": ""})
    def test_init_with_empty_api_key(self):
        """Test RapidAPIClient initialization with empty API key raises exception"""
        with pytest.raises(Exception, match="Failed to set API Key"):
            RapidAPIClient()


class TestGetJsonResponse:
    """Test suite for get_json_response function"""

    @patch("playlist_etl.extract.requests.get")
    def test_get_json_response_success(self, mock_get):
        """Test successful API response"""
        mock_response = Mock()
        mock_response.json.return_value = {"success": True, "data": ["track1", "track2"]}
        mock_get.return_value = mock_response

        result = get_json_response(
            url="https://api.example.com/playlist", host="api.example.com", api_key="test_key"
        )

        assert result == {"success": True, "data": ["track1", "track2"]}

        # Verify request was made with correct headers
        mock_get.assert_called_once_with(
            "https://api.example.com/playlist",
            headers={
                "X-RapidAPI-Key": "test_key",
                "X-RapidAPI-Host": "api.example.com",
                "Content-Type": "application/json",
            },
        )

    @patch("playlist_etl.extract.requests.get")
    def test_get_json_response_http_error(self, mock_get):
        """Test API response with HTTP error"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            get_json_response(
                url="https://api.example.com/nonexistent",
                host="api.example.com",
                api_key="test_key",
            )

    @patch("playlist_etl.extract.DEBUG_MODE", True)
    def test_get_json_response_debug_mode(self):
        """Test debug mode returns empty dict"""
        result = get_json_response(
            url="https://api.example.com/playlist", host="api.example.com", api_key="test_key"
        )

        assert result == {}

    @patch("playlist_etl.extract.NO_RAPID", True)
    def test_get_json_response_no_rapid_mode(self):
        """Test NO_RAPID mode returns empty dict"""
        result = get_json_response(
            url="https://api.example.com/playlist", host="api.example.com", api_key="test_key"
        )

        assert result == {}


class TestExtractor:
    """Test suite for Extractor class"""

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.mock_client = Mock()
        self.mock_client.api_key = "test_api_key_123"

    def test_extractor_init_spotify(self):
        """Test Extractor initialization for Spotify"""
        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        assert extractor.client == self.mock_client
        assert extractor.config == SERVICE_CONFIGS["Spotify"]
        assert extractor.base_url == SERVICE_CONFIGS["Spotify"]["base_url"]
        assert extractor.host == SERVICE_CONFIGS["Spotify"]["host"]
        assert extractor.api_key == "test_api_key_123"

    def test_extractor_init_apple_music(self):
        """Test Extractor initialization for Apple Music"""
        extractor = AppleMusicFetcher(self.mock_client, "AppleMusic", "pop")

        assert extractor.config == SERVICE_CONFIGS["AppleMusic"]
        assert extractor.base_url == SERVICE_CONFIGS["AppleMusic"]["base_url"]
        assert extractor.host == SERVICE_CONFIGS["AppleMusic"]["host"]

    def test_extractor_init_soundcloud(self):
        """Test Extractor initialization for SoundCloud"""
        extractor = SoundCloudFetcher(self.mock_client, "SoundCloud", "rap")

        assert extractor.config == SERVICE_CONFIGS["SoundCloud"]
        assert extractor.base_url == SERVICE_CONFIGS["SoundCloud"]["base_url"]
        assert extractor.host == SERVICE_CONFIGS["SoundCloud"]["host"]

    def test_extractor_init_invalid_service(self):
        """Test Extractor initialization with invalid service raises KeyError"""
        with pytest.raises(KeyError):
            Extractor(self.mock_client, "InvalidService", "dance")


class TestServiceConfigurations:
    """Test suite for service configuration validation"""

    def test_service_configs_structure(self):
        """Test that all service configs have required fields"""
        required_fields = ["base_url", "host", "param_key", "playlist_base_url", "links"]

        for service_name, config in SERVICE_CONFIGS.items():
            for field in required_fields:
                assert field in config, f"Missing {field} in {service_name} config"

    def test_service_configs_links_all_genres(self):
        """Test that all services have links for all genres"""
        for service_name, config in SERVICE_CONFIGS.items():
            for genre in PLAYLIST_GENRES:
                assert genre in config["links"], f"Missing {genre} link in {service_name}"

    def test_playlist_urls_format(self):
        """Test that playlist URLs are properly formatted"""
        for service_name, config in SERVICE_CONFIGS.items():
            for genre, url in config["links"].items():
                assert url.startswith(
                    "https://"
                ), f"Invalid URL format for {service_name} {genre}: {url}"

                # Service-specific URL validation
                if service_name == "Spotify":
                    assert "spotify.com/playlist/" in url
                elif service_name == "AppleMusic":
                    assert "music.apple.com" in url
                elif service_name == "SoundCloud":
                    assert "soundcloud.com" in url

    @pytest.mark.parametrize("service_name", list(SERVICE_CONFIGS.keys()))
    def test_service_config_completeness(self, service_name):
        """Test that each service config is complete"""
        config = SERVICE_CONFIGS[service_name]

        # Check base URL format
        assert config["base_url"].startswith("https://")

        # Check host matches URL domain
        if service_name == "AppleMusic":
            assert "apple-music24.p.rapidapi.com" in config["host"]
        elif service_name == "SoundCloud":
            assert "soundcloud-scraper.p.rapidapi.com" in config["host"]
        elif service_name == "Spotify":
            assert "spotify23.p.rapidapi.com" in config["host"]

        # Check param_key is valid
        assert isinstance(config["param_key"], str)
        assert len(config["param_key"]) > 0


class TestPlaylistGenres:
    """Test suite for playlist genre configuration"""

    def test_playlist_genres_defined(self):
        """Test that playlist genres are properly defined"""
        expected_genres = ["country", "dance", "pop", "rap"]
        assert expected_genres == PLAYLIST_GENRES

    def test_playlist_genres_match_models(self):
        """Test that playlist genres match model enums"""
        from playlist_etl.models import GenreName

        model_genres = [genre.value for genre in GenreName]
        assert set(PLAYLIST_GENRES) == set(model_genres)


class TestRealWorldScenarios:
    """Integration-style tests with realistic scenarios"""

    def setup_method(self):
        """Set up realistic test data"""
        self.mock_client = Mock()
        self.mock_client.api_key = "test_api_key_123"

    @patch("playlist_etl.extract.get_json_response")
    def test_spotify_playlist_extraction(self, mock_get_json):
        """Test realistic Spotify playlist extraction"""
        # Mock realistic Spotify API response
        spotify_response = {
            "items": [
                {
                    "track": {
                        "name": "Talk To Me",
                        "artists": [
                            {"name": "Champion"},
                            {"name": "Four Tet"},
                            {"name": "Skrillex"},
                        ],
                        "external_ids": {"isrc": "USA2P2446028"},
                        "external_urls": {
                            "spotify": "https://open.spotify.com/track/7nJVTcj5YWQVoI1vQqK7Ez"
                        },
                        "album": {
                            "images": [{"url": "https://i.scdn.co/image/ab67616d0000b273..."}]
                        },
                    }
                },
                {
                    "track": {
                        "name": "Shine On",
                        "artists": [{"name": "Kaskade"}],
                        "external_ids": {"isrc": "GB5KW2402411"},
                        "external_urls": {"spotify": "https://open.spotify.com/track/456"},
                        "album": {"images": [{"url": "https://i.scdn.co/image/def456"}]},
                    }
                },
            ]
        }

        mock_get_json.return_value = spotify_response

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        # Extract playlist data
        result = extractor.get_playlist()

        # Verify extraction results
        assert result == spotify_response

        # Verify API call was made correctly
        mock_get_json.assert_called_once()
        call_args = mock_get_json.call_args[0]  # Positional arguments
        assert len(call_args) == 3  # url, host, api_key
        assert call_args[1] == "spotify23.p.rapidapi.com"  # host is second argument
        assert call_args[2] == "test_api_key_123"  # api_key is third argument

    @patch("playlist_etl.extract.get_json_response")
    def test_apple_music_playlist_extraction(self, mock_get_json):
        """Test realistic Apple Music playlist extraction"""
        # Mock realistic Apple Music API response
        apple_response = {
            "album_details": {
                "0": {
                    "name": "Talk To Me",
                    "artist": "Champion, Four Tet, Skrillex & Naisha",
                    "link": "https://music.apple.com/us/album/talk-to-me/123",
                    "artwork": "https://is1-ssl.mzstatic.com/image/thumb/Music221/...",
                },
                "1": {
                    "name": "Shine On",
                    "artist": "Kaskade",
                    "link": "https://music.apple.com/us/album/shine-on/456",
                    "artwork": "https://is1-ssl.mzstatic.com/image/thumb/Music/...",
                },
            }
        }

        mock_get_json.return_value = apple_response

        extractor = AppleMusicFetcher(self.mock_client, "AppleMusic", "dance")

        result = extractor.get_playlist()

        assert result == apple_response

        # Verify Apple Music specific parameters
        mock_get_json.assert_called_once()
        call_args = mock_get_json.call_args[0]  # Positional arguments
        assert len(call_args) == 3  # url, host, api_key
        assert call_args[1] == "apple-music24.p.rapidapi.com"  # host is second argument

    @patch("playlist_etl.extract.get_json_response")
    def test_soundcloud_playlist_extraction(self, mock_get_json):
        """Test realistic SoundCloud playlist extraction"""
        # Mock realistic SoundCloud API response
        soundcloud_response = {
            "tracks": {
                "items": [
                    {
                        "title": "Champion - Talk To Me",
                        "user": {"name": "Champion"},
                        "publisher": {"isrc": "USA2P2446028"},
                        "permalink": "https://soundcloud.com/champion/talk-to-me",
                        "artworkUrl": "https://i1.sndcdn.com/artworks-abc123",
                    },
                    {
                        "title": "Shine On",
                        "user": {"name": "Kaskade"},
                        "publisher": {"isrc": "GB5KW2402411"},
                        "permalink": "https://soundcloud.com/kaskade/shine-on",
                        "artworkUrl": "https://i1.sndcdn.com/artworks-def456",
                    },
                ]
            }
        }

        mock_get_json.return_value = soundcloud_response

        extractor = SoundCloudFetcher(self.mock_client, "SoundCloud", "dance")

        result = extractor.get_playlist()

        assert result == soundcloud_response

        # Verify SoundCloud specific parameters
        mock_get_json.assert_called_once()
        call_args = mock_get_json.call_args[0]  # Positional arguments
        assert len(call_args) == 3  # url, host, api_key
        assert call_args[1] == "soundcloud-scraper.p.rapidapi.com"  # host is second argument

    @patch("playlist_etl.extract.get_json_response")
    def test_extraction_with_api_error(self, mock_get_json):
        """Test extraction handles API errors gracefully"""
        mock_get_json.side_effect = requests.HTTPError("Rate limit exceeded")

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        with pytest.raises(requests.HTTPError):
            extractor.get_playlist()

    @patch("playlist_etl.extract.get_json_response")
    def test_extraction_with_empty_response(self, mock_get_json):
        """Test extraction handles empty API responses"""
        mock_get_json.return_value = {}

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        result = extractor.get_playlist()
        assert result == {}

    @pytest.mark.parametrize(
        "service_name,genre",
        [
            ("Spotify", "dance"),
            ("AppleMusic", "pop"),
            ("SoundCloud", "rap"),
            ("Spotify", "country"),
        ],
    )
    @patch("playlist_etl.extract.get_json_response")
    def test_all_service_genre_combinations(self, mock_get_json, service_name, genre):
        """Test extraction works for all service/genre combinations"""
        mock_get_json.return_value = {"test": "data"}

        # Select appropriate fetcher class based on service
        fetcher_classes = {
            "Spotify": SpotifyFetcher,
            "AppleMusic": AppleMusicFetcher,
            "SoundCloud": SoundCloudFetcher,
        }
        fetcher_class = fetcher_classes[service_name]
        extractor = fetcher_class(self.mock_client, service_name, genre)
        result = extractor.get_playlist()

        assert result == {"test": "data"}
        assert mock_get_json.called

    def test_url_construction_spotify(self):
        """Test URL construction for Spotify playlists"""

        playlist_id = "37i9dQZF1DX4dyzvuaRJ0n"  # From dance playlist URL
        expected_url = f"https://spotify23.p.rapidapi.com/playlist_tracks/?id={playlist_id}"

        # Test URL construction logic (assuming method exists)
        config = SERVICE_CONFIGS["Spotify"]
        base_url = config["base_url"]
        param_key = config["param_key"]
        playlist_url = config["links"]["dance"]

        # Extract playlist ID from URL
        extracted_id = playlist_url.split("/")[-1]
        constructed_url = f"{base_url}?{param_key}={extracted_id}"

        assert extracted_id == playlist_id
        assert constructed_url == expected_url

    def test_url_construction_apple_music(self):
        """Test URL construction for Apple Music playlists"""

        config = SERVICE_CONFIGS["AppleMusic"]
        playlist_url = config["links"]["pop"]

        # Apple Music URLs should be passed as-is to the API
        assert playlist_url.startswith("https://music.apple.com/us/playlist/")

    def test_url_construction_soundcloud(self):
        """Test URL construction for SoundCloud playlists"""

        config = SERVICE_CONFIGS["SoundCloud"]
        playlist_url = config["links"]["country"]

        # SoundCloud URLs should be passed as-is to the API
        assert playlist_url.startswith("https://soundcloud.com/")
        assert "/sets/" in playlist_url  # SoundCloud playlist format


class TestErrorHandling:
    """Test suite for error handling scenarios"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_client = Mock()
        self.mock_client.api_key = "test_api_key"

    @patch("playlist_etl.extract.get_json_response")
    def test_network_timeout_handling(self, mock_get_json):
        """Test handling of network timeouts"""
        mock_get_json.side_effect = requests.Timeout("Request timeout")

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        with pytest.raises(requests.Timeout):
            extractor.get_playlist()

    @patch("playlist_etl.extract.get_json_response")
    def test_invalid_json_response(self, mock_get_json):
        """Test handling of invalid JSON responses"""
        # Mock get_json_response to raise JSONDecodeError (as would happen in real scenario)
        mock_get_json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        # Should propagate JSONDecodeError from get_json_response
        with pytest.raises(json.JSONDecodeError):
            extractor.get_playlist()

    @patch("playlist_etl.extract.get_json_response")
    def test_rate_limit_handling(self, mock_get_json):
        """Test handling of API rate limits"""
        rate_limit_response = Mock()
        rate_limit_response.status_code = 429
        rate_limit_response.raise_for_status.side_effect = requests.HTTPError(
            "429 Too Many Requests"
        )

        mock_get_json.side_effect = requests.HTTPError("429 Too Many Requests")

        extractor = SpotifyFetcher(self.mock_client, "Spotify", "dance")

        with pytest.raises(requests.HTTPError):
            extractor.get_playlist()


class TestRunExtraction:
    """Test suite for run_extraction function with MongoDB mocking"""

    def setup_method(self):
        """Set up test fixtures"""
        self.mock_mongo_client = Mock()
        self.mock_api_client = Mock()
        self.mock_api_client.api_key = "test_api_key"

    @patch("playlist_etl.extract.insert_or_update_data_to_mongo")
    @patch("playlist_etl.extract.get_json_response")
    @patch("playlist_etl.extract.requests.get")
    def test_run_extraction_spotify_end_to_end(
        self, mock_requests_get, mock_get_json, mock_mongo_insert
    ):
        """Test complete run_extraction flow for Spotify with MongoDB mocking"""
        # Mock Spotify playlist page response for set_playlist_details
        mock_spotify_page = Mock()
        mock_spotify_page.raise_for_status.return_value = None
        mock_spotify_page.text = """
        <html>
            <meta property="og:title" content="Today's Top Hits">
            <meta property="og:image" content="https://i.scdn.co/image/cover.jpg">
            <div>Cover: The hottest tracks right now</div>
        </html>
        """
        mock_requests_get.return_value = mock_spotify_page

        # Mock Spotify API response
        spotify_api_response = {
            "tracks": {
                "items": [
                    {
                        "track": {
                            "name": "As It Was",
                            "artists": [{"name": "Harry Styles"}],
                            "external_ids": {"isrc": "GBK3W2200037"},
                            "album": {"images": [{"url": "https://i.scdn.co/image/album.jpg"}]},
                        }
                    }
                ]
            }
        }
        mock_get_json.return_value = spotify_api_response

        # Run the extraction
        run_extraction(self.mock_mongo_client, self.mock_api_client, "Spotify", "dance")

        # Verify MongoDB insertion was called
        mock_mongo_insert.assert_called_once()
        call_args = mock_mongo_insert.call_args
        assert call_args[0][0] == self.mock_mongo_client  # mongo_client
        assert call_args[0][1] == "raw_playlists"  # collection_name

        # Verify document structure
        document = call_args[0][2]
        assert document["service_name"] == "Spotify"
        assert document["genre_name"] == "dance"
        assert document["data_json"] == spotify_api_response
        assert document["playlist_name"] == "Today's Top Hits"
        assert "playlist_cover_url" in document

    @patch("playlist_etl.extract.insert_or_update_data_to_mongo")
    @patch("playlist_etl.extract.get_json_response")
    @patch("playlist_etl.extract.requests.get")
    @patch("playlist_etl.extract.WebDriverManager")
    def test_run_extraction_apple_music_end_to_end(
        self, mock_webdriver, mock_requests_get, mock_get_json, mock_mongo_insert
    ):
        """Test complete run_extraction flow for Apple Music with MongoDB mocking"""
        # Mock Apple Music playlist page response
        mock_apple_page = Mock()
        mock_apple_page.raise_for_status.return_value = None
        mock_apple_page.text = """
        <html>
            <meta property="og:title" content="Today's Hits">
            <meta name="description" content="The biggest songs right now">
            <meta property="og:image" content="https://is1-ssl.mzstatic.com/image/thumb/cover.jpg">
        </html>
        """
        mock_requests_get.return_value = mock_apple_page

        # Mock Apple Music API response
        apple_api_response = {
            "tracks": [
                {
                    "name": "Anti-Hero",
                    "artist": "Taylor Swift",
                    "isrc": "USUG12204277",
                    "albumCover": "https://is1-ssl.mzstatic.com/image/thumb/album.jpg",
                }
            ]
        }
        mock_get_json.return_value = apple_api_response

        # Run the extraction
        run_extraction(self.mock_mongo_client, self.mock_api_client, "AppleMusic", "pop")

        # Verify MongoDB insertion was called with correct data
        mock_mongo_insert.assert_called_once()
        call_args = mock_mongo_insert.call_args
        document = call_args[0][2]
        assert document["service_name"] == "AppleMusic"
        assert document["genre_name"] == "pop"
        assert document["data_json"] == apple_api_response

    @patch("playlist_etl.extract.DEBUG_MODE", True)
    @patch("playlist_etl.extract.insert_or_update_data_to_mongo")
    @patch("playlist_etl.extract.get_json_response")
    @patch("playlist_etl.extract.requests.get")
    def test_run_extraction_debug_mode_skips_mongo(
        self, mock_requests_get, mock_get_json, mock_mongo_insert
    ):
        """Test that DEBUG_MODE=True skips MongoDB insertion"""
        # Mock the web scraping and API calls
        mock_page = Mock()
        mock_page.raise_for_status.return_value = None
        mock_page.text = '<html><meta property="og:title" content="Test Playlist"></html>'
        mock_requests_get.return_value = mock_page
        mock_get_json.return_value = {"test": "data"}

        # Run extraction in debug mode
        run_extraction(self.mock_mongo_client, self.mock_api_client, "Spotify", "dance")

        # Verify MongoDB insertion was NOT called
        mock_mongo_insert.assert_not_called()

    def test_run_extraction_invalid_service_raises_error(self):
        """Test that invalid service name raises ValueError"""
        with pytest.raises(ValueError, match="Unknown service: InvalidService"):
            run_extraction(self.mock_mongo_client, self.mock_api_client, "InvalidService", "dance")


# Note: Tests mock both external API calls and MongoDB operations
# This ensures unit tests run independently without external dependencies
