import time
from typing import List, Dict
from datetime import datetime

import logging
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from utils import Spotify, get_selenium_webdriver

from utils import (
    MongoClient,
    Spotify,
    clear_collection,
    collection_is_empty,
    get_mongo_client,
    get_spotify_client,
    insert_or_update_data_to_mongo,
    set_secrets,
    read_data_from_mongo
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


AGGREGATED_DATA_COLLECTION = "aggregated_playlists"
VIEW_COUNTS_COLLECTION = "view_counts_playlists"
CURRENT_TIMESTAMP = datetime.now().isoformat()
SERVICE_NAMES = ["Spotify"]

def initialize_new_view_count_playlists(mongo_client: MongoClient) -> None:
    if collection_is_empty(VIEW_COUNTS_COLLECTION, mongo_client):
        aggregated_playlists = read_data_from_mongo(mongo_client, AGGREGATED_DATA_COLLECTION)
        for playlist in aggregated_playlists:
            insert_or_update_data_to_mongo(mongo_client, VIEW_COUNTS_COLLECTION, playlist)

def update_view_counts(playlists: List[Dict], mongo_client: MongoClient):
    for playlist in playlists:
        logging.info(f"updating view counts for {playlist['genre_name']}")
        for track in playlist["tracks"]:
            for service_name in SERVICE_NAMES:
                if "view_count_data_json" not in track:
                    track["view_count_data_json"] = {}
                    track["view_count_data_json"][service_name] = {}
                
                current_view_count = get_view_count(track["isrc"], service_name)
                if "initial_count_json" not in track["view_count_data_json"][service_name]:
                    track["view_count_data_json"][service_name]["initial_count_json"] = {
                        "initial_timestamp": CURRENT_TIMESTAMP,
                        "initial_view_count":  current_view_count, 
                    }

                track["view_count_data_json"][service_name]["current_count_json"] = {
                    "current_timestamp": CURRENT_TIMESTAMP,
                    "current_view_count":  current_view_count, 
                }
                
                initial_view_count = track["view_count_data_json"][service_name]["initial_count_json"]["initial_view_count"]
                percentage_change = calculate_percentage_change(initial_view_count, current_view_count)
                track["view_count_data_json"][service_name]["percentage_change"] = percentage_change
        
        for service_name in SERVICE_NAMES:         
            playlist["tracks"].sort(key=lambda t: t["view_count_data_json"][service_name]["percentage_change"], reverse=True)

            for rank, track in enumerate(playlist["tracks"], start=1):
                track[f"{service_name.lower()}_relative_view_count_rank"] = rank
            
            playlist["tracks"].sort(key=lambda t: t["view_count_data_json"][service_name]["current_count_json"]["current_view_count"], reverse=True)

            for rank, track in enumerate(playlist["tracks"], start=1):
                track[f"{service_name.lower()}_total_view_count_rank"] = rank

        insert_or_update_data_to_mongo(mongo_client, VIEW_COUNTS_COLLECTION, playlist)
    
def get_view_count(isrc: str, service_name: str) -> int:
    match service_name:
        case "Spotify":
            return get_spotify_track_view_count(isrc, spotify_client)
        case _:
            raise ValueError("Unexpected service name")
  
def get_spotify_track_view_count(isrc: str, spotify_client: Spotify) -> int:
    url = get_spotify_track_url(isrc, spotify_client)
    xpath = "//span[contains(@class, 'encore-text') and contains(@class, 'encore-text-body-small') and contains(@class, 'RANLXG3qKB61Bh3') and @data-testid='playcount']"
    play_count_info = find_element_by_xpath(url, xpath)
    print(play_count_info)
    if not play_count_info:
        raise ValueError(f"Could not find play count for {isrc}")
    play_count = int(play_count_info.replace(",", ""))
    return play_count

def get_spotify_track_url(isrc: str, spotify_client: Spotify) -> str:
    logging.info(f"Searching for track with ISRC: {isrc}")
    results = spotify_client.search(q=f"isrc:{isrc}", type="track", limit=1)
    tracks = results["tracks"]["items"]
    if tracks:
        track_id = tracks[0]["id"]
        track_url = f"https://open.spotify.com/track/{track_id}"
        logging.info(f"Found track URL: {track_url}")
        return track_url
    raise ValueError(f"Could not find track for ISRC: {isrc}")

def find_element_by_xpath(url: str, xpath: str, retries: int = 3, retry_delay: int = 2) -> str:
    logging.info(f"Attempting to find element on URL: {url} using XPath: {xpath}")
    
    def attempt_find_element(use_proxy: bool) -> str:
        driver = None
        try:
            driver = get_selenium_webdriver(use_proxy)
            driver.implicitly_wait(2)
            logging.info(f"Navigating to URL: {url}")
            driver.get(url)
            
            timeout = 5
            max_timeout = 15
            start_time = time.time()
            
            while time.time() - start_time < max_timeout:
                try:
                    element = driver.find_element(By.XPATH, xpath)
                    if element and element.is_displayed():
                        element_text = element.text
                        logging.info(f"Successfully found element text: {element_text}")
                        return element_text
                except NoSuchElementException:
                    logging.info("Element not found yet, retrying...")
                    time.sleep(0.5)
            
            logging.warning("Element not found even after waiting")
            return "Element not found"
        
        except TimeoutException:
            logging.error("Timed out waiting for element")
            return "Timed out waiting for element"
        except NoSuchElementException:
            logging.error("Element not found on the page")
            return "Element not found on the page"
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            return f"An error occurred: {str(e)}"
        finally:
            if driver:
                logging.info("Closing Selenium WebDriver")
                driver.quit()
    
    # First attempt without proxy
    result = attempt_find_element(use_proxy=False)
    if "An error occurred" in result or result in ["Timed out waiting for element", "Element not found on the page", "Element not found"]:
        logging.info("Initial attempt failed, retrying with proxy")
        
        attempt = 1
        while attempt < retries:
            result = attempt_find_element(use_proxy=True)
            if not ("An error occurred" in result or result in ["Timed out waiting for element", "Element not found on the page", "Element not found"]):
                return result
            
            logging.info(f"Retrying with proxy... (attempt {attempt+1} of {retries})")
            time.sleep(retry_delay)
            attempt += 1
    
    return result

def calculate_percentage_change(initial_count: int, current_count: int) -> float:
    if initial_count == 0:
        return 0.0
    return ((current_count - initial_count) / initial_count) * 100
            
if __name__ == "__main__":
    set_secrets()
    mongo_client = get_mongo_client()
    clear_collection(mongo_client, VIEW_COUNTS_COLLECTION)
    initialize_new_view_count_playlists(mongo_client)
    spotify_client = get_spotify_client()
    view_counts_playlists = read_data_from_mongo(mongo_client, VIEW_COUNTS_COLLECTION)
    update_view_counts(view_counts_playlists, mongo_client)
