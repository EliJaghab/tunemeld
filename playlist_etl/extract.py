import html
import os

# Import centralized configuration
import sys
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

from playlist_etl.helpers import get_logger, set_secrets
from playlist_etl.utils import (
    WebDriverManager,
    clear_collection,
    get_mongo_client,
    insert_or_update_data_to_mongo,
)

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from config.backend.settings import tunemeld_config

PLAYLIST_GENRES = tunemeld_config.get_genres()

# Build service configs from centralized configuration
SERVICE_CONFIGS = {}
for service_key in ["appleMusic", "soundcloud", "spotify"]:
    service_config = tunemeld_config.get_service_config(service_key)
    api_config = tunemeld_config.get_service_api_config(service_key)

    if service_config and api_config:
        # Map service IDs to the format expected by this module
        service_name = (
            service_key.replace("appleMusic", "AppleMusic")
            .replace("soundcloud", "SoundCloud")
            .replace("spotify", "Spotify")
        )

        links = {}
        for genre in PLAYLIST_GENRES:
            playlist_url = tunemeld_config.get_playlist_url(service_key, genre)
            if playlist_url:
                links[genre] = playlist_url

        SERVICE_CONFIGS[service_name] = {
            "base_url": api_config.get("baseUrl", ""),
            "host": api_config.get("host", ""),
            "param_key": "url"
            if service_key == "appleMusic"
            else ("playlist" if service_key == "soundcloud" else "id"),
            "playlist_base_url": service_config.get("embedUrl", "").replace("/embed/", "/playlist/")
            if service_key == "spotify"
            else api_config.get("baseUrl", ""),
            "links": links,
        }

DEBUG_MODE = False
NO_RAPID = False


logger = get_logger(__name__)


class RapidAPIClient:
    def __init__(self):
        self.api_key = self._get_api_key()
        logger.info(f"apiKey: {self.api_key}")

    @staticmethod
    def _get_api_key():
        api_key = os.getenv("X_RAPIDAPI_KEY")
        if not api_key:
            raise Exception("Failed to set API Key.")
        return api_key


def get_json_response(url, host, api_key):
    if DEBUG_MODE or NO_RAPID:
        logger.info("Debug Mode: not requesting RapidAPI")
        return {}

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host,
        "Content-Type": "application/json",
    }
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()


class Extractor:
    def __init__(self, client, service_name, genre):
        self.client = client
        self.config = SERVICE_CONFIGS[service_name]
        self.base_url = self.config["base_url"]
        self.host = self.config["host"]
        self.api_key = self.client.api_key
        self.genre = genre
        self.playlist_param = self._prepare_param(self.config["links"][genre])
        self.param_key = self.config["param_key"]

    def _prepare_param(self, url):
        if "spotify" in self.base_url:
            return url.split("/")[-1]
        else:
            return quote(url)

    def get_playlist(self):
        raise NotImplementedError("Each service must implement its own `get_playlist` method.")


class AppleMusicFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)
        self.webdriver_manager = WebDriverManager()

    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]

        response = requests.get(url)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        title_tag = doc.select_one("a.click-action")
        title = title_tag.get_text(strip=True) if title_tag else "Unknown"

        subtitle_tag = doc.select_one("h1")
        subtitle = subtitle_tag.get_text(strip=True) if subtitle_tag else "Unknown"

        stream_tag = doc.find("amp-ambient-video", {"class": "editorial-video"})
        playlist_stream_url = stream_tag["src"] if stream_tag and stream_tag.get("src") else None

        playlist_cover_description_tag = doc.find("p", {"data-testid": "truncate-text"})
        playlist_cover_description_text = (
            unidecode(html.unescape(playlist_cover_description_tag.get_text(strip=True)))
            if playlist_cover_description_tag
            else None
        )

        self.playlist_url = url
        self.playlist_name = f"{subtitle} {title}"
        self.playlist_cover_url = self.get_cover_url(url)
        self.playlist_cover_description_text = playlist_cover_description_text
        self.playlist_stream_url = playlist_stream_url

    def get_cover_url(self, url: str) -> str:
        xpath = "//amp-ambient-video"
        src_attribute = self.webdriver_manager.find_element_by_xpath(url, xpath, attribute="src")

        if src_attribute == "Element not found" or "An error occurred" in src_attribute:
            raise ValueError(f"Could not find amp-ambient-video src attribute for Apple Music {self.genre}")

        if src_attribute.endswith(".m3u8"):
            return src_attribute
        else:
            raise ValueError(f"Found src attribute, but it's not an m3u8 URL: {src_attribute}")


class SoundCloudFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)

    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]
        parsed_url = urlparse(url)
        clean_url = f"{parsed_url.netloc}{parsed_url.path}"

        response = requests.get(f"https://{clean_url}")
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        playlist_name_tag = doc.find("meta", {"property": "og:title"})
        self.playlist_name = playlist_name_tag["content"] if playlist_name_tag else "Unknown"

        description_tag = doc.find("meta", {"name": "description"})
        self.playlist_cover_description_text = (
            description_tag["content"] if description_tag else "No description available"
        )

        playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
        self.playlist_cover_url = playlist_cover_url_tag["content"] if playlist_cover_url_tag else None

        self.playlist_url = url


class SpotifyFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)

    def get_playlist(self, offset=0, limit=100):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}&offset={offset}&limit={limit}"
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]
        response = requests.get(url)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        playlist_name_tag = doc.find("meta", {"property": "og:title"})
        self.playlist_name = playlist_name_tag["content"] if playlist_name_tag else "Unknown"

        description_div = doc.find(lambda tag: tag.name == "div" and "Cover:" in tag.get_text(strip=True))
        self.playlist_cover_description_text = (
            description_div.get_text(strip=True).replace("Spotify", " ")
            if description_div
            else "No description available"
        )

        playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
        self.playlist_cover_url = playlist_cover_url_tag["content"] if playlist_cover_url_tag else None

        self.playlist_url = url


def run_extraction(mongo_client, client, service_name, genre):
    if service_name == "AppleMusic":
        extractor = AppleMusicFetcher(client, service_name, genre)
    elif service_name == "SoundCloud":
        extractor = SoundCloudFetcher(client, service_name, genre)
    elif service_name == "Spotify":
        extractor = SpotifyFetcher(client, service_name, genre)
    else:
        raise ValueError(f"Unknown service: {service_name}")

    extractor.set_playlist_details()
    playlist_data = extractor.get_playlist()

    document = {
        "service_name": service_name,
        "genre_name": genre,
        "playlist_url": extractor.playlist_url,
        "data_json": playlist_data,
        "playlist_name": extractor.playlist_name,
        "playlist_cover_url": extractor.playlist_cover_url,
        "playlist_cover_description_text": extractor.playlist_cover_description_text,
    }

    if not DEBUG_MODE:
        insert_or_update_data_to_mongo(mongo_client, "raw_playlists", document)
    else:
        logger.info("Debug Mode: not updating mongo")


if __name__ == "__main__":
    set_secrets()
    client = RapidAPIClient()
    mongo_client = get_mongo_client()

    if DEBUG_MODE:
        logger.info("Debug Mode: not clearing mongo")
    else:
        clear_collection(mongo_client, "raw_playlists")

    for service_name, config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            logger.info(f"Retrieving {genre} from {service_name} with credential " f"{config['links'][genre]}")
            run_extraction(mongo_client, client, service_name, genre)
