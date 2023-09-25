from bs4 import BeautifulSoup
from selenium_webdriver import Driver
from constants import SOUNDCLOUD_EDM_URL
import logging

class SoundCloudExtractor:
    def __init__(self, url):
        self.url = url
        self.driver = Driver()

    def convert_soup_to_tracks(self, soup: BeautifulSoup):
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
                logging.info(f"Could not extract data for a track item due to error: {e}")
                continue
        return data
    
    def get_soundcloud_tracks(self):
        soup = self.driver.soupify_url(self.url, scroll=True)
        track_data = self.convert_soup_to_tracks(soup)
        return track_data

