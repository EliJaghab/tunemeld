from extractor import Extractor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

service = Service(executable_path='/opt/headless-chromium')


driver = webdriver.Chrome(service=service)
driver.get('https://www.google.com/')

driver.close()
driver.quit()

response = {
    "statusCode": 200,
    "body": "Selenium Headless Chrome Initialized"
}

extractor = Extractor()
print(extractor.get_soundcloud_tracks())
