from functools import lru_cache

from core.utils.config import SPOTIFY_VIEW_COUNT_XPATH
from core.utils.helpers import get_logger
from fp.fp import FreeProxy
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from webdriver_manager.chrome import ChromeDriverManager

logger = get_logger(__name__)


class WebDriverManager:
    def __init__(self) -> None:
        self.driver: WebDriver | None = None

    def get_driver(self) -> WebDriver:
        if self.driver is None:
            service = Service(ChromeDriverManager().install())
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920x1080")

            try:
                proxy = FreeProxy(rand=True, timeout=1, country_id=["US"]).get()
                chrome_options.add_argument(f"--proxy-server={proxy}")
                logger.info(f"Using proxy: {proxy}")
            except Exception as e:
                logger.warning(f"Failed to get proxy, continuing without: {e}")

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

        return self.driver

    def close_driver(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    def find_element_by_xpath(self, url: str, xpath: str, attribute: str) -> str | None:
        driver = self.get_driver()

        try:
            driver.get(url)
            element = driver.find_element(By.XPATH, xpath)
            return element.get_attribute(attribute)
        except NoSuchElementException:
            logger.error(f"Element not found with xpath: {xpath}")
            return "Element not found"
        except Exception as e:
            logger.error(f"Error finding element by xpath: {e}")
            return f"An error occurred: {e}"

    def get_spotify_track_view_count(self, track_url: str) -> int:
        driver = self.get_driver()
        driver.get(track_url)

        try:
            view_count_element = driver.find_element(By.XPATH, SPOTIFY_VIEW_COUNT_XPATH)
            view_count_text = view_count_element.text
            view_count = int(view_count_text.replace(",", ""))
            logger.info(f"Successfully retrieved Spotify view count: {view_count}")
            return view_count
        except NoSuchElementException:
            logger.error(f"View count element not found for {track_url}")
            return 0
        except Exception as e:
            logger.error(f"Error getting Spotify view count: {e}")
            return 0


@lru_cache(maxsize=1)
def get_cached_webdriver() -> WebDriverManager:
    return WebDriverManager()


def cleanup_cached_webdriver():
    webdriver = get_cached_webdriver()
    webdriver.close_driver()
    get_cached_webdriver.cache_clear()
