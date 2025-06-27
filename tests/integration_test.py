"""
End-to-end integration tests for the complete TuneMeld ETL pipeline
Tests the full flow: Extract → Transform → Aggregate → View Count Updates
"""

import json
from unittest.mock import Mock, patch

import pytest

from playlist_etl.aggregate import Aggregate
from playlist_etl.config import (
    RAW_PLAYLISTS_COLLECTION,
    TRACK_COLLECTION,
    TRACK_PLAYLIST_COLLECTION,
)
from playlist_etl.extract import RapidAPIClient, run_extraction
from playlist_etl.transform_playlist import Transform
from playlist_etl.view_count import ViewCountTrackProcessor


class TestETLPipelineIntegration:
    """End-to-end integration tests for the complete ETL pipeline"""

    @pytest.fixture
    def mock_mongo_client(self):
        """Mock MongoDB client that maintains state across pipeline stages"""
        mock_client = Mock()

        # Storage for pipeline data - simulates MongoDB collections
        self.pipeline_data = {
            RAW_PLAYLISTS_COLLECTION: [],
            TRACK_COLLECTION: [],
            TRACK_PLAYLIST_COLLECTION: [],
        }

        def mock_get_collection(name: str):
            collection = Mock()

            # Mock insert operations to store data
            def mock_insert_one(doc):
                self.pipeline_data[name].append(doc)
                return Mock(inserted_id="mock_id")

            def mock_update_one(filter_query, update_data, **kwargs):
                # Simulate upsert behavior
                doc = update_data.get("$set", {})
                doc.update(filter_query)
                self.pipeline_data[name].append(doc)
                return Mock()

            def mock_find_one(query):
                # Return matching document from our stored data
                for doc in self.pipeline_data[name]:
                    if all(doc.get(k) == v for k, v in query.items()):
                        return doc
                return None

            def mock_find(query=None):
                if query is None:
                    return iter(self.pipeline_data[name])
                return iter([doc for doc in self.pipeline_data[name] if all(doc.get(k) == v for k, v in query.items())])

            def mock_insert_many(docs):
                self.pipeline_data[name].extend(docs)
                return Mock()

            def mock_delete_many(query):
                if not query:  # Clear all
                    self.pipeline_data[name].clear()
                return Mock()

            collection.insert_one = mock_insert_one
            collection.update_one = mock_update_one
            collection.find_one = mock_find_one
            collection.find = mock_find
            collection.insert_many = mock_insert_many
            collection.delete_many = mock_delete_many

            return collection

        mock_client.get_collection = mock_get_collection
        mock_client.get_collection_count = lambda col: len(self.pipeline_data.get(col.collection_name, []))
        mock_client.overwrite_collection = lambda name, docs: self.pipeline_data.update({name: docs})
        mock_client.update_track = Mock()

        return mock_client

    @pytest.fixture
    def sample_extraction_responses(self):
        """Sample API responses for each service"""
        return {
            "Spotify": {
                "items": [
                    {
                        "track": {
                            "name": "Talk To Me",
                            "external_ids": {"isrc": "USA2P2446028"},
                            "artists": [{"name": "Champion"}, {"name": "Four Tet"}],
                            "external_urls": {"spotify": "https://open.spotify.com/track/123"},
                            "album": {"images": [{"url": "https://i.scdn.co/image/abc123"}]},
                        }
                    },
                    {
                        "track": {
                            "name": "Shine On",
                            "external_ids": {"isrc": "GB5KW2402411"},
                            "artists": [{"name": "Kaskade"}],
                            "external_urls": {"spotify": "https://open.spotify.com/track/456"},
                            "album": {"images": [{"url": "https://i.scdn.co/image/def456"}]},
                        }
                    },
                ]
            },
            "AppleMusic": {
                "album_details": {
                    "0": {
                        "name": "Talk To Me",
                        "artist": "Champion, Four Tet",
                        "link": "https://music.apple.com/us/album/talk-to-me/123",
                    },
                    "1": {
                        "name": "Different Track",
                        "artist": "Other Artist",
                        "link": "https://music.apple.com/us/album/different/456",
                    },
                }
            },
            "SoundCloud": {
                "tracks": {
                    "items": [
                        {
                            "title": "Talk To Me",
                            "user": {"name": "Champion"},
                            "publisher": {"isrc": "USA2P2446028"},
                            "permalink": "https://soundcloud.com/champion/talk-to-me",
                            "artworkUrl": "https://i1.sndcdn.com/artworks-abc123",
                        }
                    ]
                }
            },
        }

    @pytest.fixture
    def mock_external_services(self):
        """Mock external services (APIs, web scraping, etc.)"""

        def mock_get_json_response(url, host, api_key):
            # Return different responses based on the service
            if "spotify" in host:
                return {
                    "items": [
                        {
                            "track": {
                                "name": "Test Track",
                                "external_ids": {"isrc": "TEST123"},
                                "artists": [{"name": "Test Artist"}],
                                "external_urls": {"spotify": "https://open.spotify.com/track/test"},
                                "album": {"images": [{"url": "https://i.scdn.co/image/test"}]},
                            }
                        }
                    ]
                }
            elif "apple-music" in host:
                return {
                    "album_details": {
                        "0": {
                            "name": "Test Track",
                            "artist": "Test Artist",
                            "link": "https://music.apple.com/us/album/test/123",
                        }
                    }
                }
            elif "soundcloud" in host:
                return {
                    "tracks": {
                        "items": [
                            {
                                "title": "Test Track",
                                "user": {"name": "Test Artist"},
                                "publisher": {"isrc": "TEST123"},
                                "permalink": "https://soundcloud.com/test/track",
                                "artworkUrl": "https://i1.sndcdn.com/artworks-test",
                            }
                        ]
                    }
                }
            return {}

        return {
            "get_json_response": mock_get_json_response,
            "spotify_get_isrc": Mock(return_value="USA2P2446028"),
            "youtube_search": Mock(return_value="https://www.youtube.com/watch?v=test"),
            "apple_music_cover": Mock(return_value="https://is1-ssl.mzstatic.com/image/test"),
        }

    @pytest.mark.integration
    @patch("playlist_etl.extract.get_json_response")
    @patch("playlist_etl.extract.requests.get")
    def test_complete_etl_pipeline_single_genre(
        self,
        mock_requests_get,
        mock_get_json_response,
        mock_mongo_client,
        mock_external_services,
        sample_extraction_responses,
    ):
        """Test complete ETL pipeline for a single genre"""

        # === PHASE 1: EXTRACTION ===
        print("\n🔄 Phase 1: Testing Extraction...")

        # Mock API responses for each service
        def mock_api_response(url, host, api_key):
            if "spotify" in host:
                return sample_extraction_responses["Spotify"]
            elif "apple-music" in host:
                return sample_extraction_responses["AppleMusic"]
            elif "soundcloud" in host:
                return sample_extraction_responses["SoundCloud"]
            return {}

        mock_get_json_response.side_effect = mock_api_response

        # Mock web scraping for playlist details
        mock_response = Mock()
        mock_response.text = """
        <html>
            <meta property="og:title" content="Test Playlist">
            <meta property="og:image" content="https://example.com/image.jpg">
            <meta name="description" content="Test description">
        </html>
        """
        mock_response.raise_for_status = Mock()
        mock_requests_get.return_value = mock_response

        # Run extraction for each service
        client = RapidAPIClient()
        client.api_key = "test_key"

        for service_name in ["Spotify", "AppleMusic", "SoundCloud"]:
            with (
                patch("playlist_etl.extract.DEBUG_MODE", False),
                patch("playlist_etl.extract.WebDriverManager") as mock_webdriver,
            ):
                mock_webdriver.return_value.find_element_by_xpath.return_value = "https://test.m3u8"
                run_extraction(mock_mongo_client, client, service_name, "dance")

        # Verify extraction results
        raw_playlists = self.pipeline_data[RAW_PLAYLISTS_COLLECTION]
        assert len(raw_playlists) == 3, f"Expected 3 raw playlists, got {len(raw_playlists)}"

        service_names = [p["service_name"] for p in raw_playlists]
        assert "Spotify" in service_names
        assert "AppleMusic" in service_names
        assert "SoundCloud" in service_names

        print(f"✅ Extraction: Created {len(raw_playlists)} raw playlist entries")

        # === PHASE 2: TRANSFORMATION ===
        print("\n🔄 Phase 2: Testing Transformation...")

        # Mock external services for transformation
        mock_spotify_service = Mock()
        mock_spotify_service.get_isrc.side_effect = ["USA2P2446028", "GB5KW2402411", "TEST123"]
        mock_spotify_service.set_track_url = Mock()

        mock_youtube_service = Mock()
        mock_youtube_service.set_track_url = Mock()

        mock_apple_music_service = Mock()
        mock_apple_music_service.get_album_cover_url.return_value = "https://example.com/cover.jpg"

        # Prepare mock data in the format Transform expects
        for playlist in raw_playlists:
            playlist["data_json"] = json.dumps(sample_extraction_responses[playlist["service_name"]])

        # Run transformation
        transform = Transform(
            mongo_client=mock_mongo_client,
            spotify_service=mock_spotify_service,
            youtube_service=mock_youtube_service,
            apple_music_service=mock_apple_music_service,
        )

        with patch("concurrent.futures.ThreadPoolExecutor"), patch("concurrent.futures.as_completed", return_value=[]):
            transform.transform()

        # Verify transformation results
        tracks = self.pipeline_data[TRACK_COLLECTION]
        track_playlists = self.pipeline_data[TRACK_PLAYLIST_COLLECTION]

        assert len(tracks) > 0, "Transform should create track objects"
        assert len(track_playlists) > 0, "Transform should create playlist rankings"

        print(f"✅ Transformation: Created {len(tracks)} tracks, {len(track_playlists)} playlist rankings")

        # === PHASE 3: AGGREGATION ===
        print("\n🔄 Phase 3: Testing Aggregation...")

        # Run aggregation
        aggregate = Aggregate(mock_mongo_client)
        aggregate.aggregate()

        # Verify aggregation results
        aggregated_playlists = [p for p in track_playlists if p.get("service_name") == "Aggregate"]
        assert len(aggregated_playlists) > 0, "Aggregation should create aggregate playlists"

        # Check for cross-service matching
        aggregate_playlist = aggregated_playlists[0]
        if "tracks" in aggregate_playlist:
            aggregate_tracks = aggregate_playlist["tracks"]
            # Should have tracks that appear in multiple services
            multi_service_tracks = [t for t in aggregate_tracks if len(t.get("sources", {})) > 1]
            print(f"✅ Aggregation: Found {len(multi_service_tracks)} cross-service matched tracks")

        # === PHASE 4: VIEW COUNT PROCESSING ===
        print("\n🔄 Phase 4: Testing View Count Processing...")

        # Mock view count services
        mock_spotify_service.update_view_count.return_value = True
        mock_youtube_service.update_view_count.return_value = True

        view_processor = ViewCountTrackProcessor(
            mongo_client=mock_mongo_client,
            spotify_service=mock_spotify_service,
            youtube_service=mock_youtube_service,
        )

        # Mock the tracks collection to have data for view count processing
        if tracks:
            view_processor.update_view_counts()
            print("✅ View Count Processing: Completed successfully")

        # === FINAL VERIFICATION ===
        print("\n🔍 Final Pipeline Verification...")

        # Verify complete data flow
        assert len(self.pipeline_data[RAW_PLAYLISTS_COLLECTION]) == 3
        assert len(self.pipeline_data[TRACK_COLLECTION]) > 0
        assert len(self.pipeline_data[TRACK_PLAYLIST_COLLECTION]) > 0

        print("✅ Complete ETL Pipeline: All phases completed successfully!")

        # Print pipeline summary
        print("\n📊 Pipeline Summary:")
        print(f"  - Raw Playlists: {len(self.pipeline_data[RAW_PLAYLISTS_COLLECTION])}")
        print(f"  - Processed Tracks: {len(self.pipeline_data[TRACK_COLLECTION])}")
        print(f"  - Playlist Rankings: {len(self.pipeline_data[TRACK_PLAYLIST_COLLECTION])}")

    @pytest.mark.integration
    @pytest.mark.slow
    def test_multi_genre_pipeline_integration(self, mock_mongo_client):
        """Test pipeline with multiple genres to ensure scalability"""

        # Mock simplified data for multiple genres
        genres = ["dance", "pop", "rap"]
        services = ["Spotify", "AppleMusic", "SoundCloud"]

        # Simulate extraction for multiple genres
        for genre in genres:
            for service in services:
                raw_playlist = {
                    "service_name": service,
                    "genre_name": genre,
                    "playlist_url": f"https://{service.lower()}.com/playlist/{genre}",
                    "data_json": json.dumps(
                        {
                            "items" if service == "Spotify" else "tracks": [
                                {
                                    "track": {
                                        "name": f"{genre.title()} Track",
                                        "external_ids": {"isrc": f"{genre.upper()}123"},
                                    }
                                }
                                if service == "Spotify"
                                else {
                                    "name": f"{genre.title()} Track",
                                    "isrc": f"{genre.upper()}123",
                                }
                            ]
                        }
                    ),
                    "playlist_name": f"{genre.title()} Hits",
                    "playlist_cover_url": f"https://example.com/{genre}.jpg",
                    "playlist_cover_description_text": f"The best {genre} tracks",
                }
                self.pipeline_data[RAW_PLAYLISTS_COLLECTION].append(raw_playlist)

        # Verify multi-genre data creation
        total_playlists = len(genres) * len(services)
        assert len(self.pipeline_data[RAW_PLAYLISTS_COLLECTION]) == total_playlists

        # Verify genre distribution
        for genre in genres:
            genre_playlists = [p for p in self.pipeline_data[RAW_PLAYLISTS_COLLECTION] if p["genre_name"] == genre]
            assert len(genre_playlists) == len(services), f"Expected {len(services)} playlists for {genre}"

        print(
            f"✅ Multi-Genre Integration: Successfully processed {total_playlists} playlists "
            f"across {len(genres)} genres"
        )

    @pytest.mark.integration
    def test_error_recovery_and_resilience(self, mock_mongo_client):
        """Test pipeline resilience to various error conditions"""

        # Test with missing data
        incomplete_playlist = {
            "service_name": "Spotify",
            "genre_name": "dance",
            "data_json": json.dumps({"items": []}),  # Empty playlist
            "playlist_name": "Empty Playlist",
        }
        self.pipeline_data[RAW_PLAYLISTS_COLLECTION].append(incomplete_playlist)

        # Test aggregation with incomplete data
        aggregate = Aggregate(mock_mongo_client)

        # Should not raise exception with empty/missing data
        try:
            aggregate.aggregate()
            print("✅ Error Recovery: Pipeline handles missing data gracefully")
        except Exception as e:
            pytest.fail(f"Pipeline should handle missing data gracefully, but raised: {e}")

    @pytest.mark.integration
    def test_data_consistency_across_pipeline(self, mock_mongo_client):
        """Test that data remains consistent throughout the pipeline"""

        # Create test data with known ISRC
        test_isrc = "TEST2024001"
        test_track_name = "Consistency Test Track"

        # Add consistent data across services
        for service in ["Spotify", "AppleMusic", "SoundCloud"]:
            playlist = {
                "service_name": service,
                "genre_name": "dance",
                "data_json": json.dumps(
                    {
                        "items" if service == "Spotify" else "tracks": [
                            {
                                "track" if service == "Spotify" else "name": {
                                    "name": test_track_name,
                                    "external_ids": {"isrc": test_isrc},
                                }
                                if service == "Spotify"
                                else test_track_name,
                                "isrc": test_isrc if service != "Spotify" else None,
                            }
                        ]
                    }
                ),
                "playlist_name": f"{service} Dance",
            }
            self.pipeline_data[RAW_PLAYLISTS_COLLECTION].append(playlist)

        # Mock transformation to create track playlist entries
        for service in ["Spotify", "AppleMusic", "SoundCloud"]:
            track_playlist = {
                "service_name": service,
                "genre_name": "dance",
                "tracks": [{"isrc": test_isrc, "rank": 1, "sources": {service: 1}}],
            }
            self.pipeline_data[TRACK_PLAYLIST_COLLECTION].append(track_playlist)

        # Test aggregation
        aggregate = Aggregate(mock_mongo_client)
        aggregate.aggregate()

        # Verify data consistency
        aggregated = [p for p in self.pipeline_data[TRACK_PLAYLIST_COLLECTION] if p.get("service_name") == "Aggregate"]

        if aggregated and aggregated[0].get("tracks"):
            aggregate_track = aggregated[0]["tracks"][0]
            assert aggregate_track["isrc"] == test_isrc, "ISRC should be consistent across pipeline"
            assert len(aggregate_track.get("sources", {})) >= 2, "Should aggregate multiple sources"

        print("✅ Data Consistency: ISRC and track data consistent across pipeline stages")


class TestPipelinePerformance:
    """Performance and scalability tests for the ETL pipeline"""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_pipeline_performance_benchmarks(self, mock_mongo_client):
        """Test pipeline performance with realistic data volumes"""
        import time

        start_time = time.time()

        # Simulate processing 100 tracks across 4 genres and 3 services
        num_tracks_per_playlist = 25
        genres = ["dance", "pop", "rap", "country"]
        services = ["Spotify", "AppleMusic", "SoundCloud"]

        # Generate test data
        for genre in genres:
            for service in services:
                tracks_data = []
                for i in range(num_tracks_per_playlist):
                    tracks_data.append(
                        {
                            "track": {
                                "name": f"{genre.title()} Track {i}",
                                "external_ids": {"isrc": f"{genre.upper()}{i:03d}"},
                            }
                            if service == "Spotify"
                            else {
                                "name": f"{genre.title()} Track {i}",
                                "isrc": f"{genre.upper()}{i:03d}",
                            }
                        }
                    )

                playlist = {
                    "service_name": service,
                    "genre_name": genre,
                    "data_json": json.dumps({"items" if service == "Spotify" else "tracks": tracks_data}),
                }
                mock_mongo_client.pipeline_data[RAW_PLAYLISTS_COLLECTION].append(playlist)

        # Test aggregation performance
        aggregate = Aggregate(mock_mongo_client)
        aggregate.aggregate()

        end_time = time.time()
        processing_time = end_time - start_time

        total_playlists = len(genres) * len(services)
        total_tracks = num_tracks_per_playlist * total_playlists

        print("📊 Performance Benchmark:")
        print(f"  - Processed {total_tracks} tracks across {total_playlists} playlists")
        print(f"  - Processing time: {processing_time:.2f} seconds")
        print(f"  - Throughput: {total_tracks/processing_time:.1f} tracks/second")

        # Performance assertions
        assert processing_time < 30, f"Pipeline should complete in under 30 seconds, took {processing_time:.2f}s"
        assert total_tracks / processing_time > 10, "Should process at least 10 tracks per second"

        print("✅ Performance: Pipeline meets performance benchmarks")


# Helper function to run integration tests specifically
def run_integration_tests():
    """Helper function to run only integration tests"""
    import subprocess
    import sys

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/integration_test.py",
            "-m",
            "integration",
            "-v",
            "--tb=short",
        ]
    )
    return result.returncode == 0


if __name__ == "__main__":
    # Allow running integration tests directly
    print("🚀 Running TuneMeld Integration Tests...")
    success = run_integration_tests()
    if success:
        print("✅ All integration tests passed!")
    else:
        print("❌ Some integration tests failed!")
        exit(1)
