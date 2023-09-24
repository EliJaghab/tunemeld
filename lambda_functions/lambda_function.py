from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.driver_cache import DriverCacheManager

# Set the install_path to the writable /tmp directory in AWS Lambda
install_path = '/tmp'

# Initialize the DriverCacheManager with the custom install_path
cache_manager = DriverCacheManager(install_path)

# Download and install ChromeDriver using the custom cache_manager
driver_path = ChromeDriverManager(cache_manager=cache_manager).install()

# Initialize the Chrome WebDriver with the downloaded driver
driver = webdriver.Chrome(service=ChromeService(executable_path=driver_path))
driver.get("google.com")