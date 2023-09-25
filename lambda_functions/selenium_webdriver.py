from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

class Driver:
    def __init__(self):
        options = Options()
        options.binary_location = '/opt/headless-chromium'
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--single-process')
        options.add_argument('--disable-dev-shm-usage')
        
        self.driver = webdriver.Chrome('/opt/chromedriver', options=options)
    
    def retrieve_full_html(self, url, scroll = False):
        self.driver = self.get_driver()
        self.driver.get(url)

        time.sleep(2)

        if not scroll:
            return self.driver.page_source
        
        self.driver.execute_script(f"window.scrollTo(0, {self.scroll_height});")
        time.sleep(1)
        self.driver.execute_script(f"window. scrollTo(0, {self.scroll_height});")
        return self.driver.page_source

    def soupify_url(self, url, scroll = False):
        return BeautifulSoup(self.retrieve_full_html(url, scroll), features="html.parser")
    
