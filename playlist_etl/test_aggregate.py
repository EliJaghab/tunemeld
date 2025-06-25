"""
Comprehensive tests for aggregate.py
Tests cross-service track aggregation using ISRC matching with real data structures
"""

from unittest.mock import Mock

import pytest
from aggregate import Aggregate
from models import GenreName, PlaylistType, TrackSourceServiceName

from config import RANK_PRIORITY, TRACK_PLAYLIST_COLLECTION


class TestAggregate:
    """Test suite for Aggregate class"""

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.mock_mongo_client = Mock()
        self.aggregate = Aggregate(self.mock_mongo_client)

    def test_init(self):
        """Test Aggregate initialization"""
        assert self.aggregate.mongo_client == self.mock_mongo_client

    def test_group_by_genre_single_service(self, multiple_service_playlists):
        """Test grouping tracks by genre from a single service"""
        # Mock collection with single service data
        mock_collection = Mock()

        mock_collection.find_one.return_value = {
            "genre_name": "dance",
            "service_name": "Spotify",
            "tracks": [
                {"isrc": "USA2P2446028", "rank": 1, "sources": {"Spotify": 1}},
                {"isrc": "GB5KW2402411", "rank": 2, "sources": {"Spotify": 2}},
            ],
        }

        self.mock_mongo_client.get_collection.return_value = mock_collection

        # Test the grouping
        result = self.aggregate._group_by_genre(mock_collection)

        # Verify structure
        assert GenreName.DANCE in result
        assert "USA2P2446028" in result[GenreName.DANCE]
        assert "GB5KW2402411" in result[GenreName.DANCE]

        # Verify source mapping
        usa_track = result[GenreName.DANCE]["USA2P2446028"]["sources"]
        assert TrackSourceServiceName.SPOTIFY in usa_track
        assert usa_track[TrackSourceServiceName.SPOTIFY] == 1

    def test_group_by_genre_multiple_services(self, multiple_service_playlists):
        """Test grouping tracks across multiple services"""
        mock_collection = Mock()

        # Mock responses for different service/genre combinations
        def mock_find_one(query):
            service = query["service_name"]
            genre = query["genre_name"]

            if service == "Spotify" and genre == "dance":
                return {
                    "genre_name": "dance",
                    "service_name": "Spotify",
                    "tracks": [
                        {"isrc": "USA2P2446028", "rank": 1, "sources": {"Spotify": 1}},
                        {"isrc": "GB5KW2402411", "rank": 2, "sources": {"Spotify": 2}},
                    ],
                }
            elif service == "AppleMusic" and genre == "dance":
                return {
                    "genre_name": "dance",
                    "service_name": "AppleMusic",
                    "tracks": [
                        {
                            "isrc": "GB5KW2402411",
                            "rank": 1,
                            "sources": {"AppleMusic": 1},
                        },  # Same track, different rank
                        {
                            "isrc": "USA2P2446028",
                            "rank": 2,
                            "sources": {"AppleMusic": 2},
                        },  # Same track, different rank
                    ],
                }
            elif service == "SoundCloud" and genre == "dance":
                return {
                    "genre_name": "dance",
                    "service_name": "SoundCloud",
                    "tracks": [
                        {
                            "isrc": "USA2P2446028",
                            "rank": 3,
                            "sources": {"SoundCloud": 3},
                        }  # Same track, different rank
                    ],
                }
            return None

        mock_collection.find_one.side_effect = mock_find_one
        self.mock_mongo_client.get_collection.return_value = mock_collection

        result = self.aggregate._group_by_genre(mock_collection)

        # Verify cross-service aggregation
        usa_track_sources = result[GenreName.DANCE]["USA2P2446028"]["sources"]
        assert len(usa_track_sources) == 3  # Present in all 3 services
        assert usa_track_sources[TrackSourceServiceName.SPOTIFY] == 1
        assert usa_track_sources[TrackSourceServiceName.APPLE_MUSIC] == 2
        assert usa_track_sources[TrackSourceServiceName.SOUNDCLOUD] == 3

        gb_track_sources = result[GenreName.DANCE]["GB5KW2402411"]["sources"]
        assert len(gb_track_sources) == 2  # Present in 2 services
        assert gb_track_sources[TrackSourceServiceName.SPOTIFY] == 2
        assert gb_track_sources[TrackSourceServiceName.APPLE_MUSIC] == 1

    def test_get_matches_single_service_excluded(self):
        """Test that tracks from only one service are excluded from matches"""
        candidates = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "sources": {TrackSourceServiceName.SPOTIFY: 1}  # Only one source
                },
                "GB5KW2402411": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 2,
                        TrackSourceServiceName.APPLE_MUSIC: 1,  # Two sources - should match
                    }
                },
            }
        }

        result = self.aggregate._get_matches(candidates)

        # Only GB track should be in matches (has multiple sources)
        assert GenreName.DANCE in result
        assert "GB5KW2402411" in result[GenreName.DANCE]
        assert "USA2P2446028" not in result[GenreName.DANCE]  # Excluded (single source)

    def test_get_matches_multiple_services_included(self):
        """Test that tracks from multiple services are included in matches"""
        candidates = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 1,
                        TrackSourceServiceName.APPLE_MUSIC: 2,
                        TrackSourceServiceName.SOUNDCLOUD: 3,
                    }
                },
                "GB5KW2402411": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 2,
                        TrackSourceServiceName.APPLE_MUSIC: 1,
                    }
                },
            }
        }

        result = self.aggregate._get_matches(candidates)

        # Both tracks should be in matches
        assert len(result[GenreName.DANCE]) == 2
        assert "USA2P2446028" in result[GenreName.DANCE]
        assert "GB5KW2402411" in result[GenreName.DANCE]

    def test_add_aggregate_rank_priority_order(self):
        """Test aggregate ranking follows priority order: Apple Music > SoundCloud > Spotify"""
        matches = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 1,
                        TrackSourceServiceName.APPLE_MUSIC: 5,  # Lower priority rank
                        TrackSourceServiceName.SOUNDCLOUD: 2,
                    }
                },
                "GB5KW2402411": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 1,
                        TrackSourceServiceName.SOUNDCLOUD: 3,  # No Apple Music
                    }
                },
            }
        }

        result = self.aggregate._add_aggregate_rank(matches)

        # USA track should use Apple Music rank (highest priority)
        usa_track = result[GenreName.DANCE]["USA2P2446028"]
        assert usa_track["aggregate_service_name"] == TrackSourceServiceName.APPLE_MUSIC
        assert usa_track["raw_aggregate_rank"] == 5

        # GB track should use SoundCloud rank (next highest available)
        gb_track = result[GenreName.DANCE]["GB5KW2402411"]
        assert gb_track["aggregate_service_name"] == TrackSourceServiceName.SOUNDCLOUD
        assert gb_track["raw_aggregate_rank"] == 3

    def test_add_aggregate_rank_spotify_fallback(self):
        """Test fallback to Spotify when higher priority services unavailable"""
        matches = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 7  # Only Spotify available
                    }
                }
            }
        }

        result = self.aggregate._add_aggregate_rank(matches)

        usa_track = result[GenreName.DANCE]["USA2P2446028"]
        assert usa_track["aggregate_service_name"] == TrackSourceServiceName.SPOTIFY
        assert usa_track["raw_aggregate_rank"] == 7

    def test_rank_matches_sorting(self):
        """Test that matches are ranked correctly by raw_aggregate_rank"""
        matches = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "raw_aggregate_rank": 5,
                    "sources": {TrackSourceServiceName.SPOTIFY: 5},
                },
                "GB5KW2402411": {
                    "raw_aggregate_rank": 2,
                    "sources": {TrackSourceServiceName.SPOTIFY: 2},
                },
                "USUG12405639": {
                    "raw_aggregate_rank": 1,
                    "sources": {TrackSourceServiceName.SPOTIFY: 1},
                },
            }
        }

        result = self.aggregate._rank_matches(matches)

        # Verify ranking order (should be sorted by raw_aggregate_rank ascending)
        tracks = list(result[GenreName.DANCE].values())

        # Find tracks by their raw_aggregate_rank for verification
        rank_1_track = next(t for t in tracks if t["raw_aggregate_rank"] == 1)
        rank_2_track = next(t for t in tracks if t["raw_aggregate_rank"] == 2)
        rank_5_track = next(t for t in tracks if t["raw_aggregate_rank"] == 5)

        assert rank_1_track["rank"] == 1  # Lowest raw_aggregate_rank gets rank 1
        assert rank_2_track["rank"] == 2  # Second lowest gets rank 2
        assert rank_5_track["rank"] == 3  # Highest gets rank 3

    def test_format_aggregated_playlist(self):
        """Test formatting of aggregated playlist data"""
        sorted_matches = {
            GenreName.DANCE: {
                "USA2P2446028": {
                    "rank": 1,
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 1,
                        TrackSourceServiceName.APPLE_MUSIC: 2,
                    },
                    "raw_aggregate_rank": 2,
                    "aggregate_service_name": TrackSourceServiceName.APPLE_MUSIC,
                },
                "GB5KW2402411": {
                    "rank": 2,
                    "sources": {TrackSourceServiceName.SPOTIFY: 2},
                    "raw_aggregate_rank": 2,
                    "aggregate_service_name": TrackSourceServiceName.SPOTIFY,
                },
            }
        }

        result = self.aggregate._format_aggregated_playlist(sorted_matches)

        # Verify structure
        assert GenreName.DANCE in result
        playlist_data = result[GenreName.DANCE]

        assert playlist_data["service_name"] == PlaylistType.AGGREGATE
        assert playlist_data["genre_name"] == GenreName.DANCE
        assert len(playlist_data["tracks"]) == 2

        # Verify track data structure
        first_track = playlist_data["tracks"][0]
        assert first_track["isrc"] == "USA2P2446028"
        assert first_track["rank"] == 1
        assert first_track["sources"] == {
            TrackSourceServiceName.SPOTIFY: 1,
            TrackSourceServiceName.APPLE_MUSIC: 2,
        }

    def test_write_aggregated_playlists(self):
        """Test writing aggregated playlists to MongoDB"""
        formatted_playlists = {
            GenreName.DANCE: {
                "service_name": PlaylistType.AGGREGATE,
                "genre_name": GenreName.DANCE,
                "tracks": [
                    {
                        "isrc": "USA2P2446028",
                        "rank": 1,
                        "sources": {TrackSourceServiceName.SPOTIFY: 1},
                    }
                ],
            }
        }

        mock_collection = Mock()
        self.mock_mongo_client.get_collection.return_value = mock_collection

        self.aggregate._write_aggregated_playlists(formatted_playlists)

        # Verify MongoDB operations
        self.mock_mongo_client.get_collection.assert_called_with(TRACK_PLAYLIST_COLLECTION)
        mock_collection.update_one.assert_called_once()

        # Verify update_one call parameters
        call_args = mock_collection.update_one.call_args
        filter_query = call_args[0][0]
        update_data = call_args[0][1]
        upsert_flag = call_args[1]["upsert"]

        assert filter_query == {
            "service_name": PlaylistType.AGGREGATE.value,
            "genre_name": GenreName.DANCE.value,
        }
        assert update_data["$set"] == formatted_playlists[GenreName.DANCE]
        assert upsert_flag is True

    def test_aggregate_end_to_end(self, multiple_service_playlists):
        """Test complete aggregation pipeline end-to-end"""
        # Mock the track_playlists collection
        mock_collection = Mock()

        def mock_find_one(query):
            service = query["service_name"]
            genre = query["genre_name"]
            # Handle enum values - convert to string values for key lookup
            service_str = service.value if hasattr(service, "value") else str(service)
            genre_str = genre.value if hasattr(genre, "value") else str(genre)
            key = f"{service_str.lower()}_{genre_str}"
            return multiple_service_playlists.get(key)

        mock_collection.find_one.side_effect = mock_find_one
        self.mock_mongo_client.get_collection.return_value = mock_collection

        # Run the complete aggregation
        self.aggregate.aggregate()

        # Verify all steps were called
        assert self.mock_mongo_client.get_collection.called
        assert mock_collection.find_one.call_count > 0  # Should query multiple service/genre combos
        assert mock_collection.update_one.called  # Should write results

    def test_aggregate_empty_playlists(self):
        """Test aggregation with empty playlists"""
        mock_collection = Mock()
        mock_collection.find_one.return_value = {
            "genre_name": "dance",
            "service_name": "Spotify",
            "tracks": [],  # Empty tracks list
        }
        self.mock_mongo_client.get_collection.return_value = mock_collection

        # Should not raise exception with empty data
        self.aggregate.aggregate()

        # With empty tracks, no matches are found, so no writes should occur
        # This is correct behavior - empty playlists don't generate aggregate data
        assert not mock_collection.update_one.called

    def test_aggregate_missing_playlist(self):
        """Test aggregation when playlist is not found"""
        mock_collection = Mock()
        mock_collection.find_one.return_value = None  # Playlist not found
        self.mock_mongo_client.get_collection.return_value = mock_collection

        # Should handle missing playlists gracefully without raising exceptions
        self.aggregate.aggregate()  # Should complete without error

        # No playlists found means no data to write
        assert not mock_collection.update_one.called

    @pytest.mark.parametrize("genre", list(GenreName))
    def test_aggregate_all_genres(self, genre):
        """Test aggregation works for all supported genres"""
        mock_collection = Mock()
        mock_collection.find_one.return_value = {
            "genre_name": genre.value,
            "service_name": "Spotify",
            "tracks": [{"isrc": "TEST123", "rank": 1, "sources": {"Spotify": 1}}],
        }
        self.mock_mongo_client.get_collection.return_value = mock_collection

        # Should work for any genre
        self.aggregate.aggregate()

        # Verify genre was processed
        calls = mock_collection.find_one.call_args_list
        genre_queries = [call[0][0]["genre_name"] for call in calls]
        assert genre in genre_queries

    def test_rank_priority_configuration(self):
        """Test that RANK_PRIORITY configuration is respected"""
        # This test verifies the priority order from config

        expected_order = [
            TrackSourceServiceName.APPLE_MUSIC,
            TrackSourceServiceName.SOUNDCLOUD,
            TrackSourceServiceName.SPOTIFY,
        ]

        assert expected_order == RANK_PRIORITY

        # Test with all services present
        matches = {
            GenreName.DANCE: {
                "TEST123": {
                    "sources": {
                        TrackSourceServiceName.SPOTIFY: 1,  # Should be lowest priority
                        TrackSourceServiceName.SOUNDCLOUD: 2,  # Should be middle priority
                        TrackSourceServiceName.APPLE_MUSIC: 3,  # Should be highest priority
                    }
                }
            }
        }

        result = self.aggregate._add_aggregate_rank(matches)
        track = result[GenreName.DANCE]["TEST123"]

        # Should choose Apple Music despite it having the highest rank number
        assert track["aggregate_service_name"] == TrackSourceServiceName.APPLE_MUSIC
        assert track["raw_aggregate_rank"] == 3


class TestAggregateIntegration:
    """Integration tests for Aggregate with real-like data scenarios"""

    def test_realistic_aggregation_scenario(self):
        """Test aggregation with realistic multi-service data"""
        mock_mongo_client = Mock()
        mock_collection = Mock()

        # Realistic scenario: Different services have different top tracks
        realistic_data = {
            ("Spotify", "dance"): {
                "genre_name": "dance",
                "service_name": "Spotify",
                "tracks": [
                    {
                        "isrc": "USA2P2446028",
                        "rank": 1,
                        "sources": {"Spotify": 1},
                    },  # Talk To Me - #1 on Spotify
                    {
                        "isrc": "GB5KW2402411",
                        "rank": 2,
                        "sources": {"Spotify": 2},
                    },  # Shine On - #2 on Spotify
                    {
                        "isrc": "USUG12405639",
                        "rank": 3,
                        "sources": {"Spotify": 3},
                    },  # Move - #3 on Spotify
                ],
            },
            ("AppleMusic", "dance"): {
                "genre_name": "dance",
                "service_name": "AppleMusic",
                "tracks": [
                    {
                        "isrc": "GB5KW2402411",
                        "rank": 1,
                        "sources": {"AppleMusic": 1},
                    },  # Shine On - #1 on Apple Music
                    {
                        "isrc": "USUG12405639",
                        "rank": 2,
                        "sources": {"AppleMusic": 2},
                    },  # Move - #2 on Apple Music
                    {
                        "isrc": "USA2P2446028",
                        "rank": 5,
                        "sources": {"AppleMusic": 5},
                    },  # Talk To Me - #5 on Apple Music
                ],
            },
            ("SoundCloud", "dance"): {
                "genre_name": "dance",
                "service_name": "SoundCloud",
                "tracks": [
                    {
                        "isrc": "USUG12405639",
                        "rank": 1,
                        "sources": {"SoundCloud": 1},
                    },  # Move - #1 on SoundCloud
                    {
                        "isrc": "USA2P2446028",
                        "rank": 4,
                        "sources": {"SoundCloud": 4},
                    },  # Talk To Me - #4 on SoundCloud
                ],
            },
        }

        def mock_find_one(query):
            key = (query["service_name"], query["genre_name"])
            return realistic_data.get(key)

        mock_collection.find_one.side_effect = mock_find_one
        mock_mongo_client.get_collection.return_value = mock_collection

        aggregate = Aggregate(mock_mongo_client)
        aggregate.aggregate()

        # Verify the aggregation was processed and written
        assert mock_collection.update_one.called

        # Check that upsert was used for creating/updating aggregate playlists
        call_args = mock_collection.update_one.call_args
        assert call_args[1]["upsert"] is True
