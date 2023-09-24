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
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
driver.get("http://example.com")
