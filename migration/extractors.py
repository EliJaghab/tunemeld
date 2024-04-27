import os
import json
import requests

SERVICE_CONFIGS = {
    "AppleMusic": {
        "BaseURL": "https://apple-music24.p.rapidapi.com/playlist1/",
        "Host": "apple-music24.p.rapidapi.com",
        "ParamKey": "url",
        "DancePlaylistParam": "https%3A%2F%2Fmusic.apple.com%2Fus%2Fplaylist%2Fdancexl%2Fpl.6bf4415b83ce4f3789614ac4c3675740"
    },
    "SoundCloud": {
        "BaseURL": "https://soundcloud-scraper.p.rapidapi.com/v1/playlist/tracks",
        "Host": "soundcloud-scraper.p.rapidapi.com",
        "ParamKey": "playlist",
        "DancePlaylistParam": "https%3A%2F%2Fsoundcloud.com%2Fsoundcloud-the-peak%2Fsets%2Fon-the-up-new-edm-hits"
    },
    "Spotify": {
        "BaseURL": "https://spotify23.p.rapidapi.com/playlist_tracks/",
        "Host": "spotify23.p.rapidapi.com",
        "ParamKey": "id",
        "DancePlaylistParam": "37i9dQZF1DX4dyzvuaRJ0n"
    }
}

class RapidAPIClient:
    def __init__(self):
        self.api_key = os.getenv("X_RapidAPI_Key")
        print(f"apiKey: {self.api_key}")

def get_json_response(url, host, api_key):
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": host
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise Exception(f"Error creating or executing request: {e}")

class Extractor:
    def __init__(self, client, service_name):
        self.client = client
        self.service_name = service_name
        self.config = SERVICE_CONFIGS[service_name]

    def get_playlist(self, playlist_key):
        raise NotImplementedError("Each service must implement its own `get_playlist` method.")

class AppleMusicFetcher(Extractor):
    def get_playlist(self, playlist_key):
        playlist_param = self.config[playlist_key]
        url = f"{self.config['BaseURL']}?{self.config['ParamKey']}={playlist_param}"
        return get_json_response(url, self.config['Host'], self.client.api_key)

class SoundCloudFetcher(Extractor):
    def get_playlist(self, playlist_key):
        playlist_param = self.config[playlist_key]
        url = f"{self.config['BaseURL']}?{self.config['ParamKey']}={playlist_param}"
        return get_json_response(url, self.config['Host'], self.client.api_key)

class SpotifyFetcher(Extractor):
    def get_playlist(self, playlist_key, offset=0, limit=20):  # Include pagination for Spotify
        playlist_param = self.config[playlist_key]
        url = f"{self.config['BaseURL']}?{self.config['ParamKey']}={playlist_param}&offset={offset}&limit={limit}"
        return get_json_response(url, self.config['Host'], self.client.api_key)

def write_json_to_file(data, file_path):
    """Write a Python dictionary to a JSON file."""
    try:
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)  
        return None
    except Exception as e:
        return f"Error writing JSON to file: {e}"

def format_filename(service_name, playlist_key):
    """Generate a clean file name for the JSON output."""
    base_name = f"{service_name} {playlist_key.replace('Param', '')} Extract".replace(' ', '_').lower()
    return f"{base_name}.json"

if __name__ == "__main__":
    client = RapidAPIClient()

    for service_name, config in SERVICE_CONFIGS.items():
        for key in config:
            if 'playlist' in key.lower():
                extractor_class = globals()[f"{service_name}Fetcher"]
                extractor = extractor_class(client, service_name)
                try:
                    playlist_data = extractor.get_playlist(key)
                    file_name = format_filename(service_name, key)
                    error = write_json_to_file(playlist_data, file_name)
                    if error:
                        print(f"Failed to write data to file {file_name}: {error}")
                    else:
                        print(f"Data successfully written to file {file_name}.")
                except Exception as e:
                    print(f"Failed to retrieve playlist for {service_name} using {key}: {e}")