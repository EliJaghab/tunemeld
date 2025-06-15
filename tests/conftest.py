"""
Test configuration and fixtures for TuneMeld ETL testing
Based on real MongoDB data structure analysis
"""

from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from playlist_etl.models import (
    GenreName,
)


@pytest.fixture
def mock_mongo_client():
    """Mock MongoDB client for testing"""
    mock_client = Mock()
    mock_db = Mock()
    mock_client.db = mock_db

    # Mock collections
    mock_collections = {}

    def get_collection(name: str):
        if name not in mock_collections:
            mock_collections[name] = Mock()
        return mock_collections[name]

    mock_client.get_collection = get_collection
    mock_client.get_collection_count = Mock(return_value=100)

    return mock_client


@pytest.fixture
def sample_raw_playlist_data():
    """Real raw playlist data structure from MongoDB analysis"""
    return {
        "_id": "67ba037c3fb94cda4b5e065e",
        "service_name": "Spotify",
        "genre_name": "dance",
        "playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
        "data_json": '{"tracks": [{"track_name": "Talk To Me", "artist_name": "Champion, Four Tet, Skrillex & Naisha", "track_url": "https://open.spotify.com/track/7nJVTcj5YWQVoI1vQqK7Ez", "album_cover_url": "https://i.scdn.co/image/ab67616d0000b2736e0b98630a3ae3d86a204121", "rank": 1}]}',
        "playlist_name": "Dance Hits",
        "playlist_cover_url": "https://i.scdn.co/image/ab67616d0000b273...",
        "playlist_cover_description_text": "The biggest dance tracks right now",
        "insert_timestamp": datetime.now(timezone.utc),
    }


@pytest.fixture
def sample_track_data():
    """Real track data structure from MongoDB analysis"""
    return {
        "_id": "6743d47189eeba96fa2a2b6d",
        "isrc": "USA2P2446028",
        "apple_music_track_data": {
            "service_name": "AppleMusic",
            "track_name": "Talk To Me",
            "artist_name": "Champion, Four Tet, Skrillex & Naisha",
            "track_url": "https://music.apple.com/us/album/talk-to-me/...",
            "album_cover_url": "https://is1-ssl.mzstatic.com/image/thumb/Music221/...",
        },
        "spotify_track_data": {
            "service_name": "Spotify",
            "track_name": "Talk To Me",
            "artist_name": "Champion, Four Tet, Skrillex & Naisha",
            "track_url": "https://open.spotify.com/track/7nJVTcj5YWQVoI1vQqK7Ez",
            "album_cover_url": "https://i.scdn.co/image/ab67616d0000b273...",
        },
        "soundcloud_track_data": {
            "service_name": "SoundCloud",
            "track_name": "Talk To Me",
            "artist_name": "Champion, Four Tet, Skrillex & Naisha",
            "track_url": "https://soundcloud.com/champion/talk-to-me",
            "album_cover_url": "https://i1.sndcdn.com/artworks-...",
        },
        "spotify_view": {
            "service_name": "Spotify",
            "start_view": {
                "view_count": 15420000,
                "timestamp": datetime(2024, 6, 1, tzinfo=timezone.utc),
            },
            "current_view": {"view_count": 15892340, "timestamp": datetime.now(timezone.utc)},
            "historical_view": [
                {
                    "total_view_count": 15420000,
                    "delta_view_count": 0,
                    "timestamp": datetime(2024, 6, 1, tzinfo=timezone.utc),
                },
                {
                    "total_view_count": 15892340,
                    "delta_view_count": 472340,
                    "timestamp": datetime.now(timezone.utc),
                },
            ],
        },
        "youtube_url": "https://www.youtube.com/watch?v=Zbf7WsypIkc",
        "youtube_view": {
            "service_name": "YouTube",
            "current_view": {"view_count": 8934521, "timestamp": datetime.now(timezone.utc)},
        },
    }


@pytest.fixture
def sample_track_playlist_data():
    """Real track playlist data structure from MongoDB analysis"""
    return {
        "_id": "67a78ea576216d3e9352623e",
        "service_name": "Spotify",
        "genre_name": "dance",
        "tracks": [
            {"isrc": "USA2P2446028", "rank": 1, "sources": {"Spotify": 1}},
            {"isrc": "GB5KW2402411", "rank": 2, "sources": {"Spotify": 2}},
            {"isrc": "USUG12405639", "rank": 3, "sources": {"Spotify": 3}},
        ],
    }


@pytest.fixture
def sample_aggregated_playlist_data():
    """Real aggregated playlist data structure"""
    return {
        "_id": "aggregate_dance",
        "service_name": "Aggregate",
        "genre_name": "dance",
        "tracks": [
            {
                "isrc": "USA2P2446028",
                "rank": 1,
                "sources": {"Spotify": 1, "SoundCloud": 3, "AppleMusic": 2},
                "raw_aggregate_rank": 2,
                "aggregate_service_name": "AppleMusic",
            },
            {
                "isrc": "GB5KW2402411",
                "rank": 2,
                "sources": {"Spotify": 2, "AppleMusic": 1},
                "raw_aggregate_rank": 1,
                "aggregate_service_name": "AppleMusic",
            },
        ],
    }


@pytest.fixture
def multiple_service_playlists():
    """Multiple playlists from different services for aggregation testing"""
    return {
        "spotify_dance": {
            "service_name": "Spotify",
            "genre_name": "dance",
            "tracks": [
                {"isrc": "USA2P2446028", "rank": 1, "sources": {"Spotify": 1}},
                {"isrc": "GB5KW2402411", "rank": 2, "sources": {"Spotify": 2}},
                {"isrc": "USUG12405639", "rank": 3, "sources": {"Spotify": 3}},
            ],
        },
        "applemusic_dance": {
            "service_name": "AppleMusic",
            "genre_name": "dance",
            "tracks": [
                {"isrc": "GB5KW2402411", "rank": 1, "sources": {"AppleMusic": 1}},
                {"isrc": "USA2P2446028", "rank": 2, "sources": {"AppleMusic": 2}},
                {"isrc": "USQX92405790", "rank": 3, "sources": {"AppleMusic": 3}},
            ],
        },
        "soundcloud_dance": {
            "service_name": "SoundCloud",
            "genre_name": "dance",
            "tracks": [
                {"isrc": "USQX92405790", "rank": 1, "sources": {"SoundCloud": 1}},
                {"isrc": "USUG12405639", "rank": 2, "sources": {"SoundCloud": 2}},
                {"isrc": "USA2P2446028", "rank": 3, "sources": {"SoundCloud": 3}},
            ],
        },
    }


@pytest.fixture
def cache_data():
    """Sample cache data based on real structure"""
    return {
        "isrc_cache": [
            {"key": "Talk To Me|Champion, Four Tet, Skrillex & Naisha", "value": "USA2P2446028"},
            {"key": "Shine On|Kaskade", "value": "GB5KW2402411"},
        ],
        "youtube_cache": [
            {
                "key": "Talk To Me|Champion, Four Tet, Skrillex & Naisha",
                "value": "https://www.youtube.com/watch?v=Zbf7WsypIkc",
            },
            {"key": "Shine On|Kaskade", "value": "https://www.youtube.com/watch?v=gUCy3XALejM"},
        ],
    }


@pytest.fixture
def mock_services():
    """Mock external services for testing"""
    mock_spotify = Mock()
    mock_youtube = Mock()
    mock_apple_music = Mock()

    # Mock service responses
    mock_spotify.get_track_isrc.return_value = "USA2P2446028"
    mock_youtube.search_video.return_value = "https://www.youtube.com/watch?v=Zbf7WsypIkc"
    mock_apple_music.get_album_cover.return_value = "https://is1-ssl.mzstatic.com/image/..."

    return {"spotify": mock_spotify, "youtube": mock_youtube, "apple_music": mock_apple_music}


@pytest.fixture
def real_isrc_patterns():
    """Real ISRC patterns found in data for validation testing"""
    return [
        "USA2P2446028",  # US recording
        "GB5KW2402411",  # UK recording
        "USUG12405639",  # Universal Music
        "USQX92405790",  # Other US label
        "QZRD92405763",  # Independent label
        "NLM5S2402334",  # Netherlands recording
    ]


@pytest.fixture
def genre_test_data():
    """Test data for all genres"""
    return {
        GenreName.DANCE: ["USA2P2446028", "GB5KW2402411", "USUG12405639"],
        GenreName.POP: ["USQX92405790", "QZRD92405763", "USUM72408549"],
        GenreName.RAP: ["USAT22409494", "USQX92405786", "USSM12408345"],
        GenreName.COUNTRY: ["USAT22408980", "USUG12407491", "USUM72412202"],
    }


@pytest.fixture
def error_scenarios():
    """Common error scenarios for testing"""
    return {
        "missing_isrc": {
            "track_name": "Unknown Track",
            "artist_name": "Unknown Artist",
            "isrc": None,
        },
        "invalid_url": {"youtube_url": "invalid-url", "track_url": "not-a-real-url"},
        "empty_playlist": {"service_name": "Spotify", "genre_name": "dance", "tracks": []},
        "network_timeout": Exception("Connection timeout"),
        "api_rate_limit": Exception("Rate limit exceeded"),
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "integration: marks tests as integration tests")
    config.addinivalue_line("markers", "slow: marks tests as slow running")
    config.addinivalue_line("markers", "external_api: marks tests that require external API access")
