from extractor import Extractor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium import webdriver
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

options = Options()
options.add_argument('--disable-gpu')
options.add_argument('--headless')
chrome_driver_path = "/tmp/chromedriver"

# Download and install ChromeDriver
driver_path = ChromeDriverManager(path=chrome_driver_path).install()

# Initialize the Chrome WebDriver with the downloaded driver
driver = webdriver.Chrome(executable_path=driver_path, options=options)
driver.get("http://example.com")
