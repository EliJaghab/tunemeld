import os
from urllib.parse import quote

import requests
from utils import clear_collection, get_mongo_client, insert_data_to_mongo, set_secrets

PLAYLIST_GENRES = ["dance", "rap"]

SERVICE_CONFIGS = {
    "AppleMusic": {
        "base_url": "https://apple-music24.p.rapidapi.com/playlist1/",
        "host": "apple-music24.p.rapidapi.com",
        "param_key": "url",
        "links": {
            "dance": "https://music.apple.com/us/playlist/dancexl/pl.6bf4415b83ce4f3789614ac4c3675740",  # noqa: E501
            "rap": "https://music.apple.com/us/playlist/rap-life/pl.abe8ba42278f4ef490e3a9fc5ec8e8c5",  # noqa: E501
        },
    },
    "SoundCloud": {
        "base_url": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "host": "soundcloud-scraper.p.rapidapi.com",
        "param_key": "playlist",
        "links": {
            "dance": "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits",  # noqa: E501
            "rap": "https://soundcloud.com/soundcloud-hustle/sets/drippin-best-rap-right-now",  # noqa: E501
        },
    },
    "Spotify": {
        "base_url": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "host": "spotify23.p.rapidapi.com",
        "param_key": "id",
        "links": {"dance": "37i9dQZF1DX4dyzvuaRJ0n", "rap": "37i9dQZF1DX0XUsuxWHRQd"},
    },
}


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
    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)


class SoundCloudFetcher(Extractor):
    def get_playlist(self):
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}"
        return get_json_response(url, self.host, self.api_key)


class SpotifyFetcher(Extractor):
    def get_playlist(self, offset=0, limit=100):
        url = (
            f"{self.base_url}?{self.param_key}={self.playlist_param}&"
            f"offset={offset}&limit={limit}"
        )
        return get_json_response(url, self.host, self.api_key)


def run_extraction(mongo_client, client, service_name, genre):
    if service_name == "AppleMusic":
        extractor = AppleMusicFetcher(client, service_name, genre)
    elif service_name == "SoundCloud":
        extractor = SoundCloudFetcher(client, service_name, genre)
    elif service_name == "Spotify":
        extractor = SpotifyFetcher(client, service_name, genre)
    else:
        raise ValueError(f"Unknown service: {service_name}")

    playlist_data = extractor.get_playlist()
    document = {
        "service_name": service_name,
        "genre_name": genre,
        "data_json": playlist_data,
    }
    insert_data_to_mongo(mongo_client, "raw_playlists", document)


if __name__ == "__main__":
    set_secrets()
    client = RapidAPIClient()
    mongo_client = get_mongo_client()

    # Clear the collection before starting the extraction process
    clear_collection(mongo_client, "raw_playlists")

    for service_name, config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            print(
                f"Retrieving {genre} from {service_name} with credential "
                f"{config['links'][genre]}"
            )
            run_extraction(mongo_client, client, service_name, genre)
