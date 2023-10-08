import logging
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class Driver:
    def __init__(self, headless=True):
        self.scroll_height = 20000
        self.headless = headless
        self.driver = self.initialize_driver()
        logging.info(f"Initialized driver with scroll height: {self.scroll_height}")
    
    def initialize_driver(self):
        logging.info("Initializing driver")
        options = self.get_options()
        driver = webdriver.Chrome('/opt/chromedriver', options=options)
        logging.info(f"Driver initialized with options: {options}")
        return driver

    def get_options(self):
        options = Options()
        options.binary_location = '/opt/headless-chromium'
        if self.headless:
            options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--single-process')
        options.add_argument('--disable-dev-shm-usage')
        logging.info(f"Options set: {options}")
        return options

    def retrieve_full_html(self, url, scroll = False):
        self.driver.get(url)
        logging.info(f"Retrieved HTML from URL: {url}")

        time.sleep(2)

        if not scroll:
            logging.info("Scrolling not required, returning page source")
            return self.driver.page_source
        
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        while True:
            self.driver.execute_script(f"window.scrollTo(0, {last_height});")
            time.sleep(2)
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
        logging.info("Scrolling completed, returning page source")
        return self.driver.page_source

    def soupify_url(self, url, scroll = False):
        soup = BeautifulSoup(self.retrieve_full_html(url, scroll), features="html.parser")
        logging.info(f"Soupified URL: {url}")
        return soup
