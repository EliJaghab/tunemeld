import requests
import time

from selenium import webdriver 
from selenium.webdriver.chrome.service import Service


SOUNDCLOUD_URL = "https://soundcloud.com/soundcloud-the-peak/sets/on-the-up-new-edm-hits"
APPLE_MUSIC_URL = "https://music.apple.com/us/playlist/dancexl/pl.6bf4415b83ce4f3789614ac4c3675740"
SPOTIFY_PLAYLIST_API_URL = "https://api.spotify.com/v1/playlists/37i9dQZF1DX4dyzvuaRJ0n/tracks"


CLIENT_ID = "943b6c1c8113466d8d004e148b43d857"
CLIENT_SECRET = "6b1492cd2795463097724b1a9458bf32"

class Extractor:
    def __init__(self):
        self.driver = None
        self.scroll_height = 20000
    
    def get_driver(self):
        if self.driver is None:
            # Specify the path to Chrome WebDriver executable
            webdriver_path = '/opt/chromedriver'
            
            # Create a Service object with the specified path
            service = Service(webdriver_path)
            
            # Create a Chrome WebDriver instance with the Service
            self.driver = webdriver.Chrome(service=service)
        return self.driver
    
    def retrieve_full_html(self, url, scroll = False):
        driver = self.get_driver()
        driver.get(url)

        time.sleep(2)

        if not scroll:
            return driver.page_source
        
        driver.execute_script(f"window.scrollTo(0, {self.scroll_height});")
        time.sleep(1)
        driver.execute_script(f"window. scrollTo(0, {self.scroll_height});")
        return driver.page_source
    

    def retrieve_soundcloud_items(self, soup: BeautifulSoup):
        track_items = soup.find('ul', class_='trackList__list sc-clearfix sc-list-nostyle')

        # Iterate over each track item and extract details
        data = []

        for track_item in track_items.find_all('li', recursive=True):
            try:
                # Extract track number
                track_number = track_item.find('span', class_='trackItem__number').get_text(strip=True)
                
                # Extract artist name
                artist_name = track_item.find('a', class_='trackItem__username').get_text(strip=True)
                
                # Extract song title
                song_title = track_item.find('a', class_='trackItem__trackTitle').get_text(strip=True)
                
                # Extract album cover URL
                style_attribute = track_item.find('span', class_='sc-artwork')['style']
                url = style_attribute.split('"')[1]
                
                # Storing the data in a dictionary and appending it to the list
                data.append({
                    'track_number': int(track_number),
                    'artist_name': artist_name,
                    'song_title': song_title,
                    'album_cover_url': url,
                    'source': 'SoundCloud'
                })
            except Exception as e:
                print(f"Could not extract data for a track item due to error: {e}")
                continue
        return data
    
    def get_soundcloud_tracks(self):
        return self.retrieve_soundcloud_items(self.soupify(SOUNDCLOUD_URL))

    def retrieve_apple_music_song_details(self, soup: BeautifulSoup):
        # Find all song wrappers
        song_wrappers = soup.find_all(class_='songs-list-row__song-wrapper')

        # Create a list to store each song's details
        data = []
        count = 0
        for wrapper in song_wrappers:
            try:
                # Get song title
                title = wrapper.find(attrs={"data-testid": "track-title"}).get_text(strip=True)
                
                # Get artist name(s)
                artists = ', '.join([a.get_text(strip=True) for a in wrapper.find_all(class_='click-action')])
                
                # Get the album cover URL
                img_source = wrapper.find_previous('source', type='image/jpeg')
                if img_source:
                    album_cover_url = img_source['srcset'].split(",")[1].split(" ")[0]  # Getting the higher resolution URL (80w)
                else:
                    album_cover_url = None

                count += 1
                data.append({
                    'track_number': int(count),  # We don't have track number information in your HTML snippet
                    'artist_name': artists,
                    'song_title': title,
                    'album_cover_url': album_cover_url,
                    'source': 'Apple Music'
                })

            except Exception as e:
                print(f"Could not extract data for a track item due to error: {e}")

        return data
    
class SpotifyExtractor:
    SPOTIFY_PLAYLIST_API_URL = "https://api.spotify.com/v1/playlists/37i9dQZF1DX4dyzvuaRJ0n/tracks"
    CLIENT_ID = "943b6c1c8113466d8d004e148b43d857"
    CLIENT_SECRET = "6b1492cd2795463097724b1a9458bf32"

    def authenticate_spotify(self):
        """Authenticate with the Spotify API to get the access token."""
        try:
            auth_response = requests.post(
                "https://accounts.spotify.com/api/token",
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                data={"grant_type": "client_credentials"},
                auth=(self.CLIENT_ID, self.CLIENT_SECRET),
            )
            auth_response_data = auth_response.json()
            access_token = auth_response_data["access_token"]
            return access_token
        except Exception as e:
            print(f"Failed to retrieve Spotify access token: {e}")
            return None

    def retrieve_spotify_song_details(self):
        access_token = self.authenticate_spotify()
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(self.SPOTIFY_PLAYLIST_API_URL, headers=headers)

        data = []

        if response.status_code == 200:
            track_items = response.json().get("items", [])
            
            for idx, item in enumerate(track_items):
                track = item.get("track", {})
                data.append({
                    'track_number': idx + 1,
                    'artist_name': ", ".join([artist["name"] for artist in track.get("artists", [])]),
                    'song_title': track.get("name"),
                    'album_cover_url': track.get("album", {}).get("images", [{}])[0].get("url"),
                    'source': 'Spotify'
                })
        else:
            print(f"Failed to retrieve Spotify data. HTTP Status code: {response.status_code}")

        return data