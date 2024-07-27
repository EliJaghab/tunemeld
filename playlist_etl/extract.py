import html
import os
import re
from urllib.parse import quote, urlparse

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode
from utils import (
    WebDriverManager,
    clear_collection,
    get_mongo_client,
    insert_or_update_data_to_mongo,
    set_secrets,
)

PLAYLIST_GENRES = ["country", "dance", "pop", "rap"]

SERVICE_CONFIGS = {
    "AppleMusic": {
        "base_url": "https://apple-music24.p.rapidapi.com/playlist1/",
        "host": "apple-music24.p.rapidapi.com",
        "param_key": "url",
        "playlist_base_url": "https://music.apple.com/us/playlist/",
        "links": {
            "country": "https://music.apple.com/us/playlist/todays-country/pl.87bb5b36a9bd49db8c975607452bfa2b",
            "dance": "https://music.apple.com/us/playlist/dancexl/pl.6bf4415b83ce4f3789614ac4c3675740",
            "pop": "https://music.apple.com/us/playlist/a-list-pop/pl.5ee8333dbe944d9f9151e97d92d1ead9",
            "rap": "https://music.apple.com/us/playlist/rap-life/pl.abe8ba42278f4ef490e3a9fc5ec8e8c5",
        },
    },
    "SoundCloud": {
        "base_url": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "host": "soundcloud-scraper.p.rapidapi.com",
        "param_key": "playlist",
        "playlist_base_url": "https://soundcloud.com/",
        "links": {
            "country": "https://soundcloud.com/soundcloud-shine/sets/backroads-best-country-now",
            "dance": "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits",
            "pop": "https://soundcloud.com/soundcloud-shine/sets/ear-candy-fresh-pop-picks",
            "rap": "https://soundcloud.com/soundcloud-hustle/sets/drippin-best-rap-right-now",
        },
    },
    "Spotify": {
        "base_url": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "host": "spotify23.p.rapidapi.com",
        "param_key": "id",
        "playlist_base_url": "https://open.spotify.com/playlist/",
        "links": {
            "country": "https://open.spotify.com/playlist/37i9dQZF1DX1lVhptIYRda",
            "dance": "https://open.spotify.com/playlist/37i9dQZF1DX4dyzvuaRJ0n",
            "pop": "https://open.spotify.com/playlist/37i9dQZF1DXcBWIGoYBM5M",
            "rap": "https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd",
        },
    },
}

DEBUG_MODE = False
NO_RAPID = False


class RapidAPIClient:
    def __init__(self):
        self.api_key = self._get_api_key()
        print(f"apiKey: {self.api_key}")

    @staticmethod
    def _get_api_key():
        api_key = os.getenv("X_RAPIDAPI_KEY")
        if not api_key:
            raise Exception("Failed to set API Key.")
        return api_key


def get_json_response(url, host, api_key):
    if DEBUG_MODE or NO_RAPID:
        print("Debug Mode: not requesting RapidAPI")
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
        self.driver = WebDriverManager().get_driver()

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
        self.playlist_cover_url = self.get_cover_url_with_selenium(url)
        self.playlist_cover_description_text = playlist_cover_description_text
        self.playlist_stream_url = playlist_stream_url

    def get_cover_url_with_selenium(self, url: str) -> str:
        self.driver.get(url)
        self.driver.implicitly_wait(3)
        html_content = self.driver.page_source
        self.driver.quit()

        doc = BeautifulSoup(html_content, "html.parser")

        print("Searching within amp-ambient-video tags:")
        m3u8_links = set()
        all_tags = doc.find_all()
        for tag in all_tags:
            for attr in tag.attrs:
                if isinstance(tag[attr], str):
                    links = re.findall(r"https?://\S+\.m3u8", tag[attr])
                    if links:
                        print(f"Found links in tag {tag.name} (attribute {attr}): {links}")
                        m3u8_links.update(links)

        playlist_stream_url = next(iter(m3u8_links), None)

        return playlist_stream_url


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
        self.playlist_cover_url = (
            playlist_cover_url_tag["content"] if playlist_cover_url_tag else None
        )

        self.playlist_url = url


class SpotifyFetcher(Extractor):
    def __init__(self, client, service_name, genre):
        super().__init__(client, service_name, genre)
        
    def get_playlist(self, offset=0, limit=100):
        url = (
            f"{self.base_url}?{self.param_key}={self.playlist_param}&offset={offset}&limit={limit}"
        )
        return get_json_response(url, self.host, self.api_key)

    def set_playlist_details(self):
        url = self.config["links"][self.genre]
        response = requests.get(url)
        response.raise_for_status()
        doc = BeautifulSoup(response.text, "html.parser")

        playlist_name_tag = doc.find("meta", {"property": "og:title"})
        self.playlist_name = playlist_name_tag["content"] if playlist_name_tag else "Unknown"

        description_div = doc.find(
            lambda tag: tag.name == "div" and "Cover:" in tag.get_text(strip=True)
        )
        self.playlist_cover_description_text = (
            description_div.get_text(strip=True).replace("Spotify", " ")
            if description_div
            else "No description available"
        )

        playlist_cover_url_tag = doc.find("meta", {"property": "og:image"})
        self.playlist_cover_url = (
            playlist_cover_url_tag["content"] if playlist_cover_url_tag else None
        )

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
        print("Debug Mode: not updating mongo")


if __name__ == "__main__":
    set_secrets()
    client = RapidAPIClient()
    mongo_client = get_mongo_client()

    if DEBUG_MODE:
        print("Debug Mode: not clearing mongo")
    else:
        clear_collection(mongo_client, "raw_playlists")

    for service_name, config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            print(
                f"Retrieving {genre} from {service_name} with credential "
                f"{config['links'][genre]}"
            )
            run_extraction(mongo_client, client, service_name, genre)
