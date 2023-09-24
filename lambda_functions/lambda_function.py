from extractor import Extractor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

service = Service(executable_path='/opt/headless-chromium')

service.binary_location = '/opt/headless-chromium'
service.add_argument('--headless')
service.add_argument('--no-sandbox')
service.add_argument('--single-process')
service.add_argument('--disable-dev-shm-usage')

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
