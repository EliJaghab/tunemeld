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

_webdriver_manager = None


def get_cached_webdriver() -> "WebDriverManager":
    global _webdriver_manager
    if _webdriver_manager is None:
        _webdriver_manager = WebDriverManager()
    return _webdriver_manager


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
