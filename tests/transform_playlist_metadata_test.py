import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playlist_etl.extract import PlaylistMetadata
from playlist_etl.transform_playlist_metadata import (
    transform_creator,
    transform_featured_artist,
    transform_playlist_name,
    transform_playlist_tagline,
    transform_spotify_playlist_metadata,
)


class TestSpotifyPlaylistMetadataTransformation(unittest.TestCase):
    """Test Spotify playlist metadata transformation with realistic data"""

    def test_todays_top_hits_transformation(self):
        """Test transformation of Today's Top Hits playlist data"""
        raw_metadata: PlaylistMetadata = {
            "service_name": "Spotify",
            "genre_name": "pop",
            "playlist_name": "Today's Top Hits | Spotify Playlist",
            "playlist_url": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "playlist_cover_url": "https://i.scdn.co/image/ab67706f000000025ef8ff921561760fb462f239",
            "playlist_tagline": "The hottest 50. Cover: Benson Boone",
            "playlist_featured_artist": "Benson Boone",
            "playlist_creator": "https://open.spotify.com/user/spotify",
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Verify cleaned featured artist
        self.assertEqual(result["playlist_featured_artist"], "Benson Boone")

        # Verify description text combines tagline + Cover: artist
        expected_description = "The hottest 50. Cover: Benson Boone"
        self.assertEqual(result["playlist_cover_description_text"], expected_description)

    def test_rap_caviar_no_featured_artist(self):
        """Test transformation without featured artist"""
        raw_metadata: PlaylistMetadata = {
            "service_name": "Spotify",
            "genre_name": "rap",
            "playlist_name": "RapCaviar",
            "playlist_tagline": "New music and big tracks from hip hop, rap and R&B.",
            "playlist_featured_artist": None,
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Should just be the tagline since no featured artist
        expected_description = "New music and big tracks from hip hop, rap and R&B."
        self.assertEqual(result["playlist_cover_description_text"], expected_description)
        self.assertIsNone(result["playlist_featured_artist"])

    def test_minimal_data_fallback(self):
        """Test transformation with minimal data"""
        raw_metadata: PlaylistMetadata = {
            "service_name": "Spotify",
            "genre_name": "pop",
            "playlist_name": "Unknown",
            "playlist_tagline": None,
            "playlist_featured_artist": None,
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Should use fallback description
        expected_description = "Curated playlist from Spotify."
        self.assertEqual(result["playlist_cover_description_text"], expected_description)

    def test_messy_data_cleaning(self):
        """Test transformation of messy data with artifacts"""
        raw_metadata: PlaylistMetadata = {
            "service_name": "Spotify",
            "genre_name": "country",
            "playlist_name": "Hot Country | Spotify Playlist",
            "playlist_tagline": "The hottest country music right now Spotify 2,458,672 saves",
            "playlist_featured_artist": "Luke Combs 2,458,672 saves Spotify",
            "playlist_creator": "https://open.spotify.com/user/spotifycharts",
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Verify cleaning worked
        self.assertEqual(result["playlist_featured_artist"], "Luke Combs")

        # Should combine clean tagline + clean featured artist
        expected_description = "The hottest country music right now. Cover: Luke Combs"
        self.assertEqual(result["playlist_cover_description_text"], expected_description)

    def test_only_featured_artist(self):
        """Test with only featured artist, no tagline"""
        raw_metadata: PlaylistMetadata = {
            "service_name": "Spotify",
            "genre_name": "pop",
            "playlist_tagline": None,
            "playlist_featured_artist": "Taylor Swift",
        }

        result = transform_spotify_playlist_metadata(raw_metadata)

        # Should just show Cover: artist
        expected_description = "Cover: Taylor Swift"
        self.assertEqual(result["playlist_cover_description_text"], expected_description)
        self.assertEqual(result["playlist_featured_artist"], "Taylor Swift")


class TestIndividualTransformationFunctions(unittest.TestCase):
    """Test individual transformation functions"""

    def test_transform_playlist_name(self):
        """Test playlist name cleaning"""
        self.assertEqual(transform_playlist_name("Today's Top Hits"), "Today's Top Hits")
        self.assertEqual(transform_playlist_name("Pop Mix | Spotify Playlist"), "Pop Mix")
        self.assertEqual(transform_playlist_name("Unknown"), "Untitled Playlist")
        self.assertEqual(transform_playlist_name(""), "Untitled Playlist")

    def test_transform_tagline_cleaning(self):
        """Test tagline cleaning with artifacts"""
        # Clean the Cover: part and artifacts
        messy = "The hottest 50. Cover: Benson Boone 35,672,123 saves Spotify"
        cleaned = transform_playlist_tagline(messy)
        self.assertEqual(cleaned, "The hottest 50.")

        # Multiple artifacts
        messy2 = "Great music 45,672,123 saves Spotify followers likes"
        cleaned2 = transform_playlist_tagline(messy2)
        self.assertEqual(cleaned2, "Great music.")

        # Already clean
        clean = "Perfect for any mood"
        result = transform_playlist_tagline(clean)
        self.assertEqual(result, "Perfect for any mood.")

    def test_transform_featured_artist_cleaning(self):
        """Test featured artist cleaning"""
        # With artifacts
        messy = "Taylor Swift 50,000,000 saves Spotify premium"
        cleaned = transform_featured_artist(messy)
        self.assertEqual(cleaned, "Taylor Swift")

        # Clean artist
        clean = "Ed Sheeran"
        result = transform_featured_artist(clean)
        self.assertEqual(result, "Ed Sheeran")

        # None input
        self.assertIsNone(transform_featured_artist(None))

    def test_transform_creator_formats(self):
        """Test creator transformation"""
        # URL format
        url_creator = "https://open.spotify.com/user/spotify_charts"
        result = transform_creator(url_creator)
        self.assertEqual(result, "Spotify Charts")

        # Simple username
        simple = "musiclover123"
        result = transform_creator(simple)
        self.assertEqual(result, "musiclover123")

        # None/empty fallback
        self.assertEqual(transform_creator(None), "Spotify")
        self.assertEqual(transform_creator(""), "Spotify")


if __name__ == "__main__":
    unittest.main()
