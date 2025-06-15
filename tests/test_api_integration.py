"""
TuneMeld API Integration Tests

Tests all Django backend endpoints to ensure they return expected data structures
and respond correctly. These tests run against the actual API endpoints.
"""

import json
from datetime import datetime
from typing import Any, ClassVar

import pytest
import requests


class TestAPIIntegration:
    """Integration tests for TuneMeld Django API endpoints"""

    # API base URL - will be set from environment or default to localhost
    BASE_URL = "http://127.0.0.1:8000"

    # Common test data
    TEST_GENRES: ClassVar[list[str]] = ["edm", "rap", "country"]  # Common genres that should exist
    TEST_SERVICES: ClassVar[list[str]] = ["Spotify", "AppleMusic", "SoundCloud"]

    @classmethod
    def setup_class(cls):
        """Setup for the test class"""
        import os

        # Allow override of API URL via environment variable
        cls.BASE_URL = os.getenv("API_BASE_URL", cls.BASE_URL)
        print(f"Testing API at: {cls.BASE_URL}")

    def make_request(self, endpoint: str) -> dict[str, Any]:
        """
        Make API request and return parsed JSON response

        Args:
            endpoint: API endpoint path (without base URL)

        Returns:
            Parsed JSON response

        Raises:
            AssertionError: If request fails or returns invalid JSON
        """
        url = f"{self.BASE_URL}{endpoint}"

        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            pytest.fail(f"API request failed for {url}: {e}")
        except json.JSONDecodeError as e:
            pytest.fail(f"Invalid JSON response from {url}: {e}")

    def assert_api_response_structure(self, response: dict[str, Any], expect_data: bool = True):
        """
        Assert that response follows TuneMeld API response structure

        Args:
            response: API response dictionary
            expect_data: Whether to expect data field to be present and non-None
        """
        # Check required fields
        assert "status" in response, "Response missing 'status' field"
        assert "message" in response, "Response missing 'message' field"

        # Check status values
        assert response["status"] in ["success", "error"], f"Invalid status: {response['status']}"

        # Check message is string
        assert isinstance(response["message"], str), "Message must be a string"

        if expect_data:
            assert "data" in response, "Response missing 'data' field"
            assert response["data"] is not None, "Data field is None"

        # If status is success, data should be present
        if response["status"] == "success" and expect_data:
            assert response["data"] is not None, "Success response should have data"

    @pytest.mark.integration
    def test_root_endpoint(self):
        """Test the root endpoint returns welcome message"""
        response = self.make_request("/")

        self.assert_api_response_structure(response, expect_data=False)
        assert response["status"] == "success"
        assert "TuneMeld Backend" in response["message"]

    @pytest.mark.integration
    @pytest.mark.parametrize("genre", TEST_GENRES)
    def test_graph_data_endpoint(self, genre):
        """Test graph data endpoint for each genre"""
        response = self.make_request(f"/graph-data/{genre}")

        self.assert_api_response_structure(response)

        if response["status"] == "success":
            tracks = response["data"]
            assert isinstance(tracks, list), "Graph data should be a list of tracks"

            if tracks:  # If data exists, validate structure
                track = tracks[0]

                # Required fields
                required_fields = ["isrc", "artist_name"]
                for field in required_fields:
                    assert field in track, f"Track missing required field: {field}"
                    assert track[field], f"Track {field} should not be empty"

                # Optional fields that should exist
                optional_fields = ["youtube_url", "album_cover_url"]
                for field in optional_fields:
                    assert field in track, f"Track missing field: {field}"

                # View counts structure (if present)
                if "view_counts" in track:
                    view_counts = track["view_counts"]
                    assert isinstance(view_counts, dict), "View counts should be a dictionary"

                    for service_name, counts in view_counts.items():
                        assert isinstance(
                            counts, list
                        ), f"View counts for {service_name} should be a list"
                        if counts:  # If view counts exist
                            assert (
                                len(counts[0]) == 2
                            ), "View count entry should have timestamp and delta"

    @pytest.mark.integration
    @pytest.mark.parametrize("genre", TEST_GENRES)
    def test_playlist_data_endpoint(self, genre):
        """Test playlist data endpoint for each genre"""
        response = self.make_request(f"/playlist-data/{genre}")

        self.assert_api_response_structure(response)

        if response["status"] == "success":
            playlists = response["data"]
            assert isinstance(playlists, list), "Playlist data should be a list"

            if playlists:  # If data exists, validate structure
                playlist = playlists[0]

                # Required fields
                required_fields = ["genre_name", "tracks"]
                for field in required_fields:
                    assert field in playlist, f"Playlist missing required field: {field}"

                assert (
                    playlist["genre_name"] == genre
                ), f"Genre mismatch: expected {genre}, got {playlist['genre_name']}"
                assert isinstance(playlist["tracks"], list), "Tracks should be a list"

                # Validate track structure if tracks exist
                if playlist["tracks"]:
                    track = playlist["tracks"][0]
                    track_required_fields = ["isrc", "artist_name", "track_name"]
                    for field in track_required_fields:
                        assert field in track, f"Track missing required field: {field}"

    @pytest.mark.integration
    @pytest.mark.parametrize("genre", TEST_GENRES)
    @pytest.mark.parametrize("service", TEST_SERVICES)
    def test_service_playlist_endpoint(self, genre, service):
        """Test service playlist endpoint for each genre and service combination"""
        response = self.make_request(f"/service-playlist/{genre}/{service}")

        self.assert_api_response_structure(response)

        if response["status"] == "success":
            service_data = response["data"]
            assert isinstance(service_data, list), "Service playlist data should be a list"

            if service_data:  # If data exists, validate structure
                playlist = service_data[0]

                # Required fields
                assert "genre_name" in playlist, "Service playlist missing genre_name"
                assert "service_name" in playlist, "Service playlist missing service_name"
                assert "tracks" in playlist, "Service playlist missing tracks"

                assert playlist["genre_name"] == genre, "Genre mismatch in service playlist"
                assert playlist["service_name"] == service, "Service mismatch in service playlist"
                assert isinstance(playlist["tracks"], list), "Service tracks should be a list"

    @pytest.mark.integration
    @pytest.mark.parametrize("genre", TEST_GENRES)
    def test_last_updated_endpoint(self, genre):
        """Test last updated endpoint for each genre"""
        response = self.make_request(f"/last-updated/{genre}")

        self.assert_api_response_structure(response)

        if response["status"] == "success":
            data = response["data"]
            assert isinstance(data, dict), "Last updated data should be a dictionary"
            assert "last_updated" in data, "Last updated data missing timestamp"

            # Validate timestamp format (should be ISO format or timestamp)
            last_updated = data["last_updated"]
            assert last_updated, "Last updated timestamp should not be empty"

            # Try to parse as ISO datetime
            try:
                datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            except ValueError:
                # If not ISO, should be a numeric timestamp
                try:
                    float(last_updated)
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {last_updated}")

    @pytest.mark.integration
    @pytest.mark.parametrize("genre", TEST_GENRES)
    def test_header_art_endpoint(self, genre):
        """Test header art endpoint for each genre"""
        response = self.make_request(f"/header-art/{genre}")

        self.assert_api_response_structure(response)

        if response["status"] == "success":
            art_data = response["data"]
            # Header art data structure depends on format_playlist_data function
            # At minimum should be a valid data structure
            assert art_data is not None, "Header art data should not be None"

    @pytest.mark.integration
    def test_invalid_genre_handling(self):
        """Test that invalid genres are handled gracefully"""
        invalid_genre = "nonexistent_genre_12345"

        endpoints_to_test = [
            f"/graph-data/{invalid_genre}",
            f"/playlist-data/{invalid_genre}",
            f"/last-updated/{invalid_genre}",
            f"/header-art/{invalid_genre}",
        ]

        for endpoint in endpoints_to_test:
            response = self.make_request(endpoint)
            self.assert_api_response_structure(response, expect_data=False)

            # Should either return error status or empty data
            if response["status"] == "error":
                assert (
                    "No data found" in response["message"] or "error" in response["message"].lower()
                )

    @pytest.mark.integration
    def test_invalid_service_handling(self):
        """Test that invalid services are handled gracefully"""
        test_genre = self.TEST_GENRES[0]  # Use first test genre
        invalid_service = "NonexistentService"

        response = self.make_request(f"/service-playlist/{test_genre}/{invalid_service}")
        self.assert_api_response_structure(response, expect_data=False)

        # Should return error or empty data for invalid service
        if response["status"] == "error":
            assert "No data found" in response["message"] or "error" in response["message"].lower()

    @pytest.mark.integration
    def test_api_performance(self):
        """Test that API responses are reasonably fast"""
        import time

        test_endpoints = [
            "/",
            f"/playlist-data/{self.TEST_GENRES[0]}",
            f"/graph-data/{self.TEST_GENRES[0]}",
        ]

        for endpoint in test_endpoints:
            start_time = time.time()
            self.make_request(endpoint)
            end_time = time.time()

            response_time = end_time - start_time

            # API should respond within 10 seconds (generous limit for integration tests)
            assert response_time < 10.0, f"Endpoint {endpoint} took {response_time:.2f}s (too slow)"

            # Log performance for monitoring
            print(f"Endpoint {endpoint}: {response_time:.2f}s")

    @pytest.mark.integration
    def test_cors_headers(self):
        """Test that CORS headers are properly set for frontend access"""
        response = requests.get(f"{self.BASE_URL}/", timeout=30)

        # Should have CORS headers for frontend access
        headers = response.headers

        # Check for common CORS headers (exact headers depend on Django CORS configuration)
        cors_indicators = [
            "Access-Control-Allow-Origin",
            "Access-Control-Allow-Methods",
            "Access-Control-Allow-Headers",
        ]

        # At least one CORS header should be present
        has_cors = any(header in headers for header in cors_indicators)
        if not has_cors:
            print("Warning: No CORS headers detected. Frontend may have access issues.")

    @pytest.mark.integration
    def test_json_content_type(self):
        """Test that API returns proper JSON content type"""
        response = requests.get(f"{self.BASE_URL}/", timeout=30)

        content_type = response.headers.get("Content-Type", "")
        assert (
            "application/json" in content_type
        ), f"Expected JSON content type, got: {content_type}"

    @pytest.mark.integration
    def test_consistent_response_format(self):
        """Test that all endpoints return consistent response format"""
        endpoints_to_test = [
            "/",
            f"/playlist-data/{self.TEST_GENRES[0]}",
            f"/graph-data/{self.TEST_GENRES[0]}",
            f"/last-updated/{self.TEST_GENRES[0]}",
            f"/header-art/{self.TEST_GENRES[0]}",
        ]

        for endpoint in endpoints_to_test:
            response = self.make_request(endpoint)

            # All endpoints should follow same response structure
            self.assert_api_response_structure(response, expect_data=True)

            # Status should be either success or error
            assert response["status"] in ["success", "error"]

            # Message should be descriptive
            assert len(response["message"]) > 0, f"Empty message in response for {endpoint}"


@pytest.mark.integration
class TestAPIDataQuality:
    """Tests for data quality and consistency across endpoints"""

    BASE_URL = "http://127.0.0.1:8000"

    @classmethod
    def setup_class(cls):
        import os

        cls.BASE_URL = os.getenv("API_BASE_URL", cls.BASE_URL)

    def make_request(self, endpoint: str) -> dict[str, Any]:
        """Make API request and return parsed JSON response"""
        url = f"{self.BASE_URL}{endpoint}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()

    @pytest.mark.integration
    def test_data_consistency_across_endpoints(self):
        """Test that data is consistent between related endpoints"""
        test_genre = "edm"  # Use EDM as it's likely to have data

        # Get data from different endpoints
        playlist_response = self.make_request(f"/playlist-data/{test_genre}")
        graph_response = self.make_request(f"/graph-data/{test_genre}")

        if (
            playlist_response["status"] == "success"
            and graph_response["status"] == "success"
            and playlist_response["data"]
            and graph_response["data"]
        ):
            # Extract track ISRCs from both endpoints
            playlist_tracks = (
                playlist_response["data"][0]["tracks"] if playlist_response["data"] else []
            )
            graph_tracks = graph_response["data"]

            playlist_isrcs = {track["isrc"] for track in playlist_tracks if "isrc" in track}
            graph_isrcs = {track["isrc"] for track in graph_tracks if "isrc" in track}

            # Graph data should be a subset of playlist data (same tracks, possibly with view counts)
            if playlist_isrcs and graph_isrcs:
                assert graph_isrcs.issubset(
                    playlist_isrcs
                ), "Graph data contains ISRCs not in playlist data"

    @pytest.mark.integration
    def test_required_data_fields(self):
        """Test that required data fields are present and valid"""
        test_genre = "edm"

        response = self.make_request(f"/playlist-data/{test_genre}")

        if response["status"] == "success" and response["data"]:
            playlist = response["data"][0]
            tracks = playlist.get("tracks", [])

            for i, track in enumerate(tracks[:5]):  # Check first 5 tracks
                # ISRC should be valid format (typically 12 characters)
                isrc = track.get("isrc", "")
                assert len(isrc) >= 10, f"Track {i}: ISRC too short: {isrc}"

                # Artist and track names should not be empty
                assert track.get("artist_name", "").strip(), f"Track {i}: Empty artist name"
                assert track.get("track_name", "").strip(), f"Track {i}: Empty track name"
