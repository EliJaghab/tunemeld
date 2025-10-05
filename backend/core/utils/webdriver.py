import threading

from core.utils.utils import get_logger

# ETL-only imports - conditionally imported to avoid Vercel serverless bloat
try:
    from selenium import webdriver
    from selenium.common.exceptions import NoSuchElementException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.webdriver import WebDriver
    from tenacity import retry, stop_after_attempt, wait_exponential
    from webdriver_manager.chrome import ChromeDriverManager

    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

logger = get_logger(__name__)


_thread_local = threading.local()


def get_cached_webdriver() -> "WebDriverManager":
    """Get a thread-local WebDriverManager to prevent race conditions."""
    if not hasattr(_thread_local, "webdriver_manager"):
        _thread_local.webdriver_manager = WebDriverManager()
    return _thread_local.webdriver_manager


class WebDriverManager:
    def __init__(self) -> None:
        self.driver: WebDriver | None = None

    def get_driver(self) -> WebDriver:
        if self.driver is None:
            try:
                chrome_options = Options()

                # Unified robust configuration for all environments
                chrome_options.add_argument("--headless=new")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument("--disable-gpu")
                chrome_options.add_argument("--disable-web-security")
                chrome_options.add_argument("--disable-features=VizDisplayCompositor")
                chrome_options.add_argument("--disable-extensions")
                chrome_options.add_argument("--disable-plugins")
                chrome_options.add_argument("--disable-images")
                chrome_options.add_argument("--disable-background-timer-throttling")
                chrome_options.add_argument("--disable-background-networking")
                chrome_options.add_argument("--disable-backgrounding-occluded-windows")
                chrome_options.add_argument("--disable-renderer-backgrounding")
                chrome_options.add_argument("--disable-features=TranslateUI")
                chrome_options.add_argument("--disable-ipc-flooding-protection")
                chrome_options.add_argument("--disable-logging")
                chrome_options.add_argument("--silent")
                chrome_options.add_argument("--window-size=1920x1080")

                # User agent
                chrome_options.add_argument(
                    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                # Experimental options
                chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
                chrome_options.add_experimental_option("useAutomationExtension", False)

                # Use ChromeDriverManager for automatic version matching
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)

                # Set timeouts consistently
                self.driver.implicitly_wait(10)
                self.driver.set_page_load_timeout(30)
                self.driver.set_script_timeout(30)

            except Exception as e:
                logger.error(f"Failed to initialize Chrome WebDriver: {e}")
                raise

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
