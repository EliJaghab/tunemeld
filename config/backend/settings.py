import json
import os
from pathlib import Path

# Load shared configurations
CONFIG_DIR = Path(__file__).parent.parent
SHARED_CONFIG_DIR = CONFIG_DIR / "shared"
ENVIRONMENTS_CONFIG_DIR = CONFIG_DIR / "environments"


def load_json_config(file_path):
    """Load JSON configuration file"""
    with open(file_path) as f:
        return json.load(f)


def load_environment_config():
    """Load environment-specific configuration"""
    env = os.getenv("DJANGO_ENV", "development")
    env_file = ENVIRONMENTS_CONFIG_DIR / f"{env}.json"

    if env_file.exists():
        return load_json_config(env_file)
    else:
        return load_json_config(ENVIRONMENTS_CONFIG_DIR / "development.json")


class TuneMeldBackendConfig:
    def __init__(self):
        self.genres_config = load_json_config(SHARED_CONFIG_DIR / "genres.json")
        self.services_config = load_json_config(SHARED_CONFIG_DIR / "services.json")
        self.playlists_config = load_json_config(SHARED_CONFIG_DIR / "playlists.json")
        self.constants_config = load_json_config(SHARED_CONFIG_DIR / "constants.json")
        self.env_config = load_environment_config()

    def get_genres(self):
        """Get list of all genres"""
        return [genre["id"] for genre in self.genres_config["genres"]]

    def get_genre_display_name(self, genre_id):
        """Get display name for a genre"""
        for genre in self.genres_config["genres"]:
            if genre["id"] == genre_id:
                return genre["displayName"]
        return genre_id.title()

    def get_services(self):
        """Get list of all services"""
        return list(self.services_config["services"].keys())

    def get_service_config(self, service_id):
        """Get configuration for a specific service"""
        return self.services_config["services"].get(service_id)

    def get_service_api_config(self, service_id):
        """Get API configuration for a service"""
        service = self.get_service_config(service_id)
        return service.get("api", {}) if service else {}

    def get_playlist_url(self, service, genre):
        """Get playlist URL for service and genre"""
        playlists = self.playlists_config["playlists"].get(service, {})
        return playlists.get("playlists", {}).get(genre, {}).get("url")

    def get_playlist_id(self, service, genre):
        """Get playlist ID for service and genre"""
        playlists = self.playlists_config["playlists"].get(service, {})
        return playlists.get("playlists", {}).get(genre, {}).get("id")

    def get_rank_priority(self):
        """Get service ranking priority"""
        return self.services_config["rankPriority"]

    def get_api_base_url(self):
        """Get Django API base URL"""
        return self.env_config["api"]["django"]["baseUrl"]

    def get_mongo_config(self):
        """Get MongoDB configuration"""
        return self.env_config["database"]["mongo"]

    def get_cors_origins(self):
        """Get CORS allowed origins"""
        return self.env_config["cors"]["allowedOrigins"]

    def get_allowed_hosts(self):
        """Get Django allowed hosts"""
        return self.env_config["allowedHosts"]

    def is_debug(self):
        """Check if debug mode is enabled"""
        return self.env_config.get("debug", False)

    def get_performance_config(self):
        """Get performance-related configuration"""
        return self.constants_config["performance"]

    def get_selector_config(self):
        """Get CSS/XPath selectors"""
        return self.constants_config["selectors"]

    def get_retries(self):
        """Get retry count for API calls"""
        return self.constants_config["performance"]["retries"]

    def get_retry_delay(self):
        """Get retry delay for API calls"""
        return self.constants_config["performance"]["retryDelay"]

    def get_spotify_error_threshold(self):
        """Get Spotify error threshold"""
        return self.constants_config["performance"]["spotifyErrorThreshold"]

    def get_spotify_xpath(self):
        """Get Spotify view count XPath selector"""
        return self.constants_config["selectors"]["spotifyViewCountXpath"]


# Global config instance
tunemeld_config = TuneMeldBackendConfig()

# Database collection names
PLAYLIST_ETL_DATABASE = "playlist_etl"
RAW_PLAYLISTS_COLLECTION = "raw_playlists"
TRACK_COLLECTION = "track"
TRACK_PLAYLIST_COLLECTION = "track_playlist"
ISRC_CACHE_COLLECTION = "isrc_cache"
YOUTUBE_URL_CACHE_COLLECTION = "youtube_cache"
APPLE_MUSIC_ALBUM_COVER_CACHE_COLLECTION = "apple_music_album_cover_cache"

# Additional collections
TRANSFORMED_PLAYLISTS_COLLECTION = "transformed_playlists"
PLAYLISTS_COLLECTION = "view_counts_playlists"
HISTORICAL_TRACK_VIEWS_COLLECTION = "historical_track_views"

# Export commonly used values
GENRES = tunemeld_config.get_genres()
SERVICES = tunemeld_config.get_services()
RANK_PRIORITY = tunemeld_config.get_rank_priority()
SPOTIFY_ERROR_THRESHOLD = tunemeld_config.get_spotify_error_threshold()
RETRIES = tunemeld_config.get_retries()
RETRY_DELAY = tunemeld_config.get_retry_delay()
SPOTIFY_VIEW_COUNT_XPATH = tunemeld_config.get_spotify_xpath()
