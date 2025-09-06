from core.utils.config import SPOTIFY_VIEW_COUNT_XPATH
from core.utils.utils import get_logger
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from tenacity import retry, stop_after_attempt, wait_exponential
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

            self.driver = webdriver.Chrome(service=service, options=chrome_options)

        return self.driver

    def close_driver(self) -> None:
        if self.driver:
            self.driver.quit()
            self.driver = None

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=False)
    def find_element_by_xpath(self, url: str, xpath: str, attribute: str) -> str | None:
        driver = self.get_driver()

        try:
            driver.get(url)
            element = driver.find_element(By.XPATH, xpath)
            result = element.get_attribute(attribute)
            if result:
                return result
        except NoSuchElementException:
            logger.warning(f"Element not found with xpath: {xpath}")
            raise
        except Exception as e:
            logger.warning(f"Error finding element by xpath: {e}")
            raise

        return None

    @retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3), reraise=False)
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
            raise
        except Exception as e:
            logger.error(f"Error getting Spotify view count: {e}")
            raise
