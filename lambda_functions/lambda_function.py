from extractor import Extractor
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

from selenium import webdriver
import os

def list_files_in_directory(directory):
    print(f"Listing files and directories in: {directory}")
    print(directory)  # Include the root directory itself in the output
    for root, dirs, files in os.walk(directory):
        for file in files:
            print(os.path.join(root, file))
        for dir in dirs:
            print(os.path.join(root, dir))

# List files in the Lambda execution environment's root directory
list_files_in_directory('/var/task')

# List files in the Lambda execution environment's /opt directory
list_files_in_directory('/opt')


service = Service(executable_path='/opt/chromedriver')
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")  # Run Chrome in headless mode, comment this line if you want to see the browser window
chrome_options.binary_location = '/opt/headless-chromium'    

driver = webdriver.Chrome(service=service, options = chrome_options)
driver.get('https://www.google.com/')

driver.close()
driver.quit()

response = {
    "statusCode": 200,
    "body": "Selenium Headless Chrome Initialized"
}

extractor = Extractor()
print(extractor.get_soundcloud_tracks())
