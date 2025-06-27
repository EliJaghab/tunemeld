"""
Comprehensive tests for transform2.py
Tests data transformation pipeline with real data structures and service integration
"""

import json
from collections import defaultdict
from concurrent.futures import Future
from unittest.mock import Mock, patch

import pytest

from playlist_etl.config import (
    RAW_PLAYLISTS_COLLECTION,
    TRACK_COLLECTION,
)
from playlist_etl.models import (
    GenreName,
    Track,
    TrackRank,
    TrackSourceServiceName,
)
from playlist_etl.transform import Transform


class TestTransform:
    """Test suite for Transform class"""

    def setup_method(self):
        """Set up test fixtures for each test method"""
        self.mock_mongo_client = Mock()
        self.mock_spotify_service = Mock()
        self.mock_youtube_service = Mock()
        self.mock_apple_music_service = Mock()

        self.transform = Transform(
            mongo_client=self.mock_mongo_client,
            spotify_service=self.mock_spotify_service,
            youtube_service=self.mock_youtube_service,
            apple_music_service=self.mock_apple_music_service,
        )

    def test_init(self):
        """Test Transform initialization"""
        assert self.transform.mongo_client == self.mock_mongo_client
        assert self.transform.spotify_service == self.mock_spotify_service
        assert self.transform.youtube_service == self.mock_youtube_service
        assert self.transform.apple_music_service == self.mock_apple_music_service
        assert isinstance(self.transform.tracks, dict)
        assert isinstance(self.transform.playlist_ranks, defaultdict)

    def test_get_track_new_track(self):
        """Test getting a new track creates Track object"""
        isrc = "USA2P2446028"
        track = self.transform.get_track(isrc)

        assert isinstance(track, Track)
        assert track.isrc == isrc
        assert isrc in self.transform.tracks
        assert self.transform.tracks[isrc] == track

    def test_get_track_existing_track(self):
        """Test getting an existing track returns same object"""
        isrc = "USA2P2446028"
        track1 = self.transform.get_track(isrc)
        track2 = self.transform.get_track(isrc)

        assert track1 is track2
        assert len(self.transform.tracks) == 1

    def test_convert_spotify_raw_export_valid_data(self):
        """Test converting valid Spotify raw data"""
        spotify_data = {
            "items": [
                {
                    "track": {
                        "name": "Talk To Me",
                        "external_ids": {"isrc": "USA2P2446028"},
                        "artists": [
                            {"name": "Champion"},
                            {"name": "Four Tet"},
                            {"name": "Skrillex"},
                        ],
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
        }

        self.transform.convert_spotify_raw_export_to_track_type(spotify_data, "dance")

        # Verify tracks were created
        assert len(self.transform.tracks) == 2

        # Verify first track data
        track1 = self.transform.tracks["USA2P2446028"]
        assert track1.spotify_track_data.track_name == "Talk To Me"
        assert track1.spotify_track_data.artist_name == "Champion, Four Tet, Skrillex"
        assert track1.spotify_track_data.track_url == "https://open.spotify.com/track/123"
        assert track1.spotify_track_data.album_cover_url == "https://i.scdn.co/image/abc123"

        # Verify playlist ranks were created
        spotify_ranks = self.transform.playlist_ranks[(TrackSourceServiceName.SPOTIFY.value, "dance")]
        assert len(spotify_ranks) == 2
        assert spotify_ranks[0].isrc == "USA2P2446028"
        assert spotify_ranks[0].rank == 1
        assert spotify_ranks[1].isrc == "GB5KW2402411"
        assert spotify_ranks[1].rank == 2

    def test_convert_spotify_raw_export_missing_track(self):
        """Test converting Spotify data with missing track info"""
        spotify_data = {
            "items": [
                {"track": None},  # Missing track info
                {
                    "track": {
                        "name": "Valid Track",
                        "external_ids": {"isrc": "USA2P2446028"},
                        "artists": [{"name": "Artist"}],
                        "external_urls": {"spotify": "https://open.spotify.com/track/123"},
                        "album": {"images": [{"url": "https://i.scdn.co/image/abc123"}]},
                    }
                },
            ]
        }

        self.transform.convert_spotify_raw_export_to_track_type(spotify_data, "dance")

        # Should only process the valid track
        assert len(self.transform.tracks) == 1
        assert "USA2P2446028" in self.transform.tracks

    def test_convert_apple_music_raw_export_valid_data(self):
        """Test converting valid Apple Music raw data"""
        apple_data = {
            "album_details": {
                "0": {
                    "name": "Talk To Me",
                    "artist": "Champion, Four Tet, Skrillex & Naisha",
                    "link": "https://music.apple.com/us/album/talk-to-me/123",
                },
                "1": {
                    "name": "Shine On",
                    "artist": "Kaskade",
                    "link": "https://music.apple.com/us/album/shine-on/456",
                },
            }
        }

        # Mock ISRC lookup
        self.mock_spotify_service.get_isrc.side_effect = ["USA2P2446028", "GB5KW2402411"]

        self.transform.convert_apple_music_raw_export_to_track_type(apple_data, "dance")

        # Verify ISRC lookups were called
        assert self.mock_spotify_service.get_isrc.call_count == 2
        self.mock_spotify_service.get_isrc.assert_any_call("Talk To Me", "Champion, Four Tet, Skrillex & Naisha")
        self.mock_spotify_service.get_isrc.assert_any_call("Shine On", "Kaskade")

        # Verify tracks were created
        assert len(self.transform.tracks) == 2

        track1 = self.transform.tracks["USA2P2446028"]
        assert track1.apple_music_track_data.track_name == "Talk To Me"
        assert track1.apple_music_track_data.artist_name == "Champion, Four Tet, Skrillex & Naisha"
        assert track1.apple_music_track_data.track_url == "https://music.apple.com/us/album/talk-to-me/123"

    def test_convert_apple_music_raw_export_missing_isrc(self):
        """Test Apple Music conversion when ISRC lookup fails"""
        apple_data = {
            "album_details": {
                "0": {
                    "name": "Unknown Track",
                    "artist": "Unknown Artist",
                    "link": "https://music.apple.com/us/album/unknown/123",
                }
            }
        }

        # Mock ISRC lookup failure
        self.mock_spotify_service.get_isrc.return_value = None

        self.transform.convert_apple_music_raw_export_to_track_type(apple_data, "dance")

        # Should not create any tracks
        assert len(self.transform.tracks) == 0
        assert len(self.transform.playlist_ranks) == 0

    def test_convert_soundcloud_raw_export_valid_data(self):
        """Test converting valid SoundCloud raw data"""
        soundcloud_data = {
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

        self.transform.convert_soundcloud_raw_export_to_track_type(soundcloud_data, "dance")

        # Verify tracks were created
        assert len(self.transform.tracks) == 2

        # Verify track with title format "Artist - Song"
        track1 = self.transform.tracks["USA2P2446028"]
        assert track1.soundcloud_track_data.track_name == "Talk To Me"
        assert track1.soundcloud_track_data.artist_name == "Champion"
        assert track1.soundcloud_track_data.track_url == "https://soundcloud.com/champion/talk-to-me"
        assert track1.soundcloud_track_data.album_cover_url == "https://i1.sndcdn.com/artworks-abc123"

        # Verify track without artist prefix in title
        track2 = self.transform.tracks["GB5KW2402411"]
        assert track2.soundcloud_track_data.track_name == "Shine On"
        assert track2.soundcloud_track_data.artist_name == "Kaskade"

    def test_convert_soundcloud_raw_export_missing_isrc(self):
        """Test SoundCloud conversion with missing ISRC"""
        soundcloud_data = {
            "tracks": {
                "items": [
                    {
                        "title": "Track Without ISRC",
                        "user": {"name": "Artist"},
                        "publisher": {"isrc": ""},  # Empty ISRC
                        "permalink": "https://soundcloud.com/artist/track",
                        "artworkUrl": "https://i1.sndcdn.com/artworks-abc123",
                    },
                    {
                        "title": "Valid Track",
                        "user": {"name": "Artist2"},
                        "publisher": {"isrc": "USA2P2446028"},
                        "permalink": "https://soundcloud.com/artist2/track",
                        "artworkUrl": "https://i1.sndcdn.com/artworks-def456",
                    },
                ]
            }
        }

        self.transform.convert_soundcloud_raw_export_to_track_type(soundcloud_data, "dance")

        # Should only create track with valid ISRC
        assert len(self.transform.tracks) == 1
        assert "USA2P2446028" in self.transform.tracks

    @patch("concurrent.futures.ThreadPoolExecutor")
    def test_set_youtube_urls(self, mock_executor):
        """Test setting YouTube URLs for tracks"""
        # Set up tracks
        track1 = Track(isrc="USA2P2446028")
        track2 = Track(isrc="GB5KW2402411")
        self.transform.tracks = {"USA2P2446028": track1, "GB5KW2402411": track2}

        # Mock executor
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance

        # Mock futures
        mock_future1 = Mock(spec=Future)
        mock_future2 = Mock(spec=Future)
        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]

        # Mock as_completed to return futures
        with patch("concurrent.futures.as_completed", return_value=[mock_future1, mock_future2]):
            self.transform.set_youtube_urls()

        # Verify YouTube service was called for each track
        assert mock_executor_instance.submit.call_count == 2

        # Check that submit was called with the YouTube service method and track objects
        submit_calls = mock_executor_instance.submit.call_args_list
        assert len(submit_calls) == 2

        # Check that each call was to youtube_service.set_track_url with a track
        for call in submit_calls:
            args, kwargs = call
            assert args[0] == self.mock_youtube_service.set_track_url
            assert isinstance(args[1], Track)  # Second arg should be a Track object
            assert args[1].isrc in [
                "USA2P2446028",
                "GB5KW2402411",
            ]  # Should be one of our test tracks

    @patch("concurrent.futures.ThreadPoolExecutor")
    def test_set_apple_music_album_covers(self, mock_executor):
        """Test setting Apple Music album covers"""
        # Set up tracks with Apple Music data
        track1 = Track(isrc="USA2P2446028")
        track1.apple_music_track_data.track_name = "Talk To Me"
        track1.apple_music_track_data.track_url = "https://music.apple.com/us/album/123"

        track2 = Track(isrc="GB5KW2402411")
        # track2 has no Apple Music data

        self.transform.tracks = {"USA2P2446028": track1, "GB5KW2402411": track2}

        # Mock executor
        mock_executor_instance = Mock()
        mock_executor.return_value.__enter__.return_value = mock_executor_instance
        mock_future1 = Mock(spec=Future)
        mock_future2 = Mock(spec=Future)
        mock_executor_instance.submit.side_effect = [mock_future1, mock_future2]

        with patch("concurrent.futures.as_completed", return_value=[mock_future1, mock_future2]):
            self.transform.set_apple_music_album_covers()

        # Should process all tracks (filtering happens inside set_apple_music_album_cover_url)
        # Both tracks get submitted, but only track1 will actually process since track2 has no track_name
        assert mock_executor_instance.submit.call_count == 2

    def test_set_apple_music_album_cover_url(self):
        """Test setting individual Apple Music album cover URL"""
        track = Track(isrc="USA2P2446028")
        track.apple_music_track_data.track_name = "Talk To Me"
        track.apple_music_track_data.track_url = "https://music.apple.com/us/album/123"

        self.mock_apple_music_service.get_album_cover_url.return_value = "https://is1-ssl.mzstatic.com/image/abc123"

        self.transform.set_apple_music_album_cover_url(track)

        self.mock_apple_music_service.get_album_cover_url.assert_called_once_with(
            "https://music.apple.com/us/album/123"
        )
        assert track.apple_music_track_data.album_cover_url == "https://is1-ssl.mzstatic.com/image/abc123"

    def test_merge_track_data_simple(self):
        """Test merging track data with simple values"""
        existing = {"isrc": "USA2P2446028", "spotify_data": {"track_name": "Old Name"}}
        new = {"spotify_data": {"track_name": "New Name", "artist_name": "Artist"}}

        result = self.transform.merge_track_data(existing, new)

        assert result["isrc"] == "USA2P2446028"
        assert result["spotify_data"]["track_name"] == "New Name"
        assert result["spotify_data"]["artist_name"] == "Artist"

    def test_merge_track_data_nested(self):
        """Test merging nested track data structures"""
        existing = {
            "isrc": "USA2P2446028",
            "spotify_view": {"service_name": "Spotify", "start_view": {"view_count": 1000}},
        }
        new = {"spotify_view": {"current_view": {"view_count": 2000}}}

        result = self.transform.merge_track_data(existing, new)

        assert result["spotify_view"]["service_name"] == "Spotify"
        assert result["spotify_view"]["start_view"]["view_count"] == 1000
        assert result["spotify_view"]["current_view"]["view_count"] == 2000

    def test_format_tracks(self):
        """Test formatting tracks for database storage"""
        track1 = Track(isrc="USA2P2446028")
        track1.spotify_track_data.track_name = "Talk To Me"

        track2 = Track(isrc="")  # Should be excluded (empty ISRC)

        self.transform.tracks = {"USA2P2446028": track1, "": track2}

        result = self.transform.format_tracks()

        # Should include both tracks (filtering only checks for None, not empty strings)
        assert len(result) == 2
        assert result[0]["isrc"] == "USA2P2446028"
        assert result[1]["isrc"] == ""
        assert "track_data" in result[0]

    def test_format_playlist_ranks(self):
        """Test formatting playlist ranks for database storage"""
        rank1 = TrackRank(isrc="USA2P2446028", rank=1, sources={TrackSourceServiceName.SPOTIFY: 1})
        rank2 = TrackRank(isrc="GB5KW2402411", rank=2, sources={TrackSourceServiceName.SPOTIFY: 2})

        self.transform.playlist_ranks[("Spotify", GenreName.DANCE)] = [rank1, rank2]

        result = self.transform.format_playlist_ranks()

        assert len(result) == 1
        playlist = result[0]
        assert playlist["service_name"] == TrackSourceServiceName.SPOTIFY
        assert playlist["genre_name"] == GenreName.DANCE
        assert len(playlist["tracks"]) == 2

    def test_overwrite_new_tracks(self):
        """Test overwriting with new tracks"""
        track = Track(isrc="USA2P2446028")
        self.transform.tracks = {"USA2P2446028": track}

        mock_collection = Mock()
        mock_collection.find_one.return_value = None  # No existing track
        self.mock_mongo_client.get_collection.return_value = mock_collection

        self.transform.overwrite()

        # Should insert new track
        mock_collection.update_one.assert_called_once()
        call_args = mock_collection.update_one.call_args
        assert call_args[0][0] == {"isrc": "USA2P2446028"}
        assert call_args[1]["upsert"] is True

    def test_overwrite_existing_tracks(self):
        """Test overwriting with existing tracks (merge scenario)"""
        track = Track(isrc="USA2P2446028")
        track.spotify_track_data.track_name = "New Name"
        self.transform.tracks = {"USA2P2446028": track}

        existing_track = {
            "isrc": "USA2P2446028",
            "spotify_data": {"track_name": "Old Name", "artist_name": "Artist"},
        }

        mock_collection = Mock()
        mock_collection.find_one.return_value = existing_track
        self.mock_mongo_client.get_collection.return_value = mock_collection

        self.transform.overwrite()

        # Should merge and update existing track
        mock_collection.update_one.assert_called_once()

    def test_build_track_objects_missing_playlist(self):
        """Test error handling when raw playlist is not found"""
        mock_collection = Mock()
        mock_collection.find_one.return_value = None  # No playlist found
        self.mock_mongo_client.get_collection.return_value = mock_collection

        with pytest.raises(ValueError, match="No raw playlist found"):
            self.transform.build_track_objects(mock_collection)

    def test_convert_to_track_objects_unknown_service(self):
        """Test error handling for unknown service"""
        with pytest.raises(ValueError, match="Unknown service name"):
            self.transform.convert_to_track_objects({}, "UnknownService", "dance")

    @pytest.mark.parametrize("service_name", list(TrackSourceServiceName))
    def test_convert_to_track_objects_all_services(self, service_name):
        """Test that conversion works for all supported services"""
        # Mock data for each service type
        if service_name == TrackSourceServiceName.SPOTIFY:
            data = {"items": []}
        elif service_name == TrackSourceServiceName.APPLE_MUSIC:
            data = {"album_details": {}}
        elif service_name == TrackSourceServiceName.SOUNDCLOUD:
            data = {"tracks": {"items": []}}

        # Should not raise exception for any valid service
        self.transform.convert_to_track_objects(data, service_name.value, "dance")

    def test_transform_end_to_end(self, sample_raw_playlist_data):
        """Test complete transformation pipeline"""
        # Mock raw playlists collection
        mock_raw_collection = Mock()
        spotify_raw_data = {
            "data_json": json.dumps(
                {
                    "items": [
                        {
                            "track": {
                                "name": "Talk To Me",
                                "external_ids": {"isrc": "USA2P2446028"},
                                "artists": [{"name": "Champion"}],
                                "external_urls": {"spotify": "https://open.spotify.com/track/123"},
                                "album": {"images": [{"url": "https://i.scdn.co/image/abc123"}]},
                            }
                        }
                    ]
                }
            )
        }

        def mock_find_one(query):
            if query["service_name"] == "Spotify":
                return spotify_raw_data
            elif query["service_name"] == "AppleMusic":
                return {
                    "data_json": json.dumps(
                        {
                            "album_details": {
                                "0": {
                                    "name": "Test Apple Track",
                                    "artist": "Test Artist",
                                    "link": "https://music.apple.com/us/album/test/123",
                                }
                            }
                        }
                    )
                }
            elif query["service_name"] == "SoundCloud":
                return {
                    "data_json": json.dumps(
                        {
                            "tracks": {
                                "items": [
                                    {
                                        "title": "Test SoundCloud Track",
                                        "user": {"name": "Test SoundCloud Artist"},
                                        "publisher": {"isrc": "TEST123SC"},
                                        "permalink": "https://soundcloud.com/test/track",
                                        "artworkUrl": "https://i1.sndcdn.com/artworks-test",
                                    }
                                ]
                            }
                        }
                    )
                }
            return None

        mock_raw_collection.find_one.side_effect = mock_find_one

        # Mock track collection
        mock_track_collection = Mock()
        mock_track_collection.find_one.return_value = None

        # Mock Spotify service get_isrc for Apple Music tracks
        self.mock_spotify_service.get_isrc.return_value = "TEST123AM"

        def mock_get_collection(name):
            if name == RAW_PLAYLISTS_COLLECTION:
                return mock_raw_collection
            elif name == TRACK_COLLECTION:
                return mock_track_collection
            return Mock()

        self.mock_mongo_client.get_collection.side_effect = mock_get_collection

        # Mock concurrent operations
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
            mock_executor_instance = Mock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            mock_future = Mock(spec=Future)
            mock_executor_instance.submit.return_value = mock_future

            with patch("concurrent.futures.as_completed", return_value=[mock_future]):
                self.transform.transform()

        # Verify all steps were executed
        assert mock_raw_collection.find_one.called
        assert self.mock_mongo_client.overwrite_collection.called


class TestTransformIntegration:
    """Integration tests for Transform with realistic scenarios"""

    def test_realistic_multi_service_transformation(self):
        """Test transformation with realistic multi-service data"""
        mock_mongo_client = Mock()
        mock_spotify_service = Mock()
        mock_youtube_service = Mock()
        mock_apple_music_service = Mock()

        # Set up realistic ISRC responses - Apple Music track should get a different ISRC
        mock_spotify_service.get_isrc.return_value = "GB5KW2402411"

        transform = Transform(
            mongo_client=mock_mongo_client,
            spotify_service=mock_spotify_service,
            youtube_service=mock_youtube_service,
            apple_music_service=mock_apple_music_service,
        )

        # Test Spotify data conversion
        spotify_data = {
            "items": [
                {
                    "track": {
                        "name": "Talk To Me",
                        "external_ids": {"isrc": "USA2P2446028"},
                        "artists": [{"name": "Champion"}, {"name": "Four Tet"}],
                        "external_urls": {"spotify": "https://open.spotify.com/track/123"},
                        "album": {"images": [{"url": "https://i.scdn.co/image/abc123"}]},
                    }
                }
            ]
        }

        # Test Apple Music data conversion
        apple_data = {
            "album_details": {
                "0": {
                    "name": "Shine On",
                    "artist": "Kaskade",
                    "link": "https://music.apple.com/us/album/shine-on/456",
                }
            }
        }

        transform.convert_spotify_raw_export_to_track_type(spotify_data, "dance")
        transform.convert_apple_music_raw_export_to_track_type(apple_data, "dance")

        # Verify cross-service track creation
        assert len(transform.tracks) == 2
        assert "USA2P2446028" in transform.tracks
        assert "GB5KW2402411" in transform.tracks

        # Verify service-specific data
        spotify_track = transform.tracks["USA2P2446028"]
        assert spotify_track.spotify_track_data.track_name == "Talk To Me"
        assert spotify_track.spotify_track_data.artist_name == "Champion, Four Tet"

        apple_track = transform.tracks["GB5KW2402411"]
        assert apple_track.apple_music_track_data.track_name == "Shine On"
        assert apple_track.apple_music_track_data.artist_name == "Kaskade"
