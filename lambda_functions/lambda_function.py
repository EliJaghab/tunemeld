from extractor import Extractor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

driverpath = Service("/opt/chromedriver.exe") #add your own path
try: 
    driver = webdriver.Chrome(service=driverpath)
except:
    driverpath = Service("/opt/chromedriver") #add your own path
    driver = webdriver.Chrome(service=driverpath)

driver.get('https://www.google.com/')

extractor = Extractor()
print(extractor.get_soundcloud_tracks())
