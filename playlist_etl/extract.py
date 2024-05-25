import os
import json
import requests
import subprocess

EXTRACT_BASE_PATH = "docs/files/extract"
SCRIPT_PATH = "api_credentials.sh"

PLAYLIST_GENRES = ["dance_playlist_key"]

SERVICE_CONFIGS = {
    "AppleMusic": {
        "base_url": "https://apple-music24.p.rapidapi.com/playlist1/",
        "host": "apple-music24.p.rapidapi.com",
        "param_key": "url",
        "dance_playlist_key": "https%3A%2F%2Fmusic.apple.com%2Fus%2Fplaylist%2Fdancexl%2Fpl.6bf4415b83ce4f3789614ac4c3675740",
    },
    "SoundCloud": {
        "base_url": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "host": "soundcloud-scraper.p.rapidapi.com",
        "param_key": "playlist",
        "dance_playlist_key": "https%3A%2F%2Fsoundcloud.com%2Fsoundcloud-the-peak%2Fsets%2Fon-the-up-new-edm-hits",
    },
    "Spotify": {
        "base_url": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "host": "spotify23.p.rapidapi.com",
        "param_key": "id",
        "dance_playlist_key": "37i9dQZF1DX4dyzvuaRJ0n",
    },
}


class RapidAPIClient:
    def __init__(self):
        self.api_key = self.get_api_key()
        print(f"apiKey: {self.api_key}")

    def get_api_key(self):
        api_key = os.getenv("X_RapidAPI_Key")
        if not api_key and not os.getenv("GITHUB_ACTIONS"):
            load_env_variables_from_script()
            api_key = os.getenv("X_RapidAPI_Key")
        if not api_key:
            raise Exception("Failed to set API Key.")
        return api_key


def load_env_variables_from_script():
    result = subprocess.Popen(
        ["bash", "-c", f"source {SCRIPT_PATH} && env"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = result.communicate()

    if result.returncode != 0:
        raise Exception(f"Script failed to execute cleanly: {stderr.decode()}")

    for line in stdout.decode().splitlines():
        key, _, value = line.partition("=")
        os.environ[key] = value


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
        self.playlist_param = self.config[genre]
        self.param_key = self.config["param_key"]

    def get_playlist(self):
        raise NotImplementedError(
            "Each service must implement its own `get_playlist` method."
        )


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
        url = f"{self.base_url}?{self.param_key}={self.playlist_param}&offset={offset}&limit={limit}"
        return get_json_response(url, self.host, self.api_key)


def write_json_to_file(data, file_path):
    """Write a Python dictionary to a JSON file."""
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)
    print(f"wrote to {file_path}")


def format_filename(service_name, playlist_key):
    """Generate a clean file name for the JSON output."""
    base_name = (
        f"{service_name}_{playlist_key.replace('playlist_key', '')}extract".lower()
    )
    full_path = f"{EXTRACT_BASE_PATH}/{base_name}.json"
    os.makedirs(EXTRACT_BASE_PATH, exist_ok=True)
    return full_path


if __name__ == "__main__":

    client = RapidAPIClient()

    for service_name, config in SERVICE_CONFIGS.items():
        for genre in PLAYLIST_GENRES:
            playlist_key = config[genre]

            print(
                f"retrieving {genre} from {service_name} with credential {playlist_key}"
            )
            extractor_class = globals()[f"{service_name}Fetcher"]
            extractor = extractor_class(client, service_name, genre)
            playlist_data = extractor.get_playlist()
            file_name = format_filename(service_name, genre)
            write_json_to_file(playlist_data, file_name)
