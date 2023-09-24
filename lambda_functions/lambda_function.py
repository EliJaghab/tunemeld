from extractor import Extractor
from extractor import webdriver


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--disable-dev-tools')
chrome_options.add_argument('--remote-debugging-port=9222')
chrome_options.add_argument('--window-size=1280x1696')
chrome_options.add_argument('--user-data-dir=/tmp/chrome-user-data')
chrome_options.add_argument('--single-process')
chrome_options.add_argument("--no-zygote")
chrome_options.add_argument('--ignore-certificate-errors')
chrome_options.binary_location = "/opt/chrome/chrome"

driver = webdriver.Chrome
driver = webdriver.Chrome("/opt/chromedriver",options=chrome_options)
driver.get('https://www.google.com/')

extractor = Extractor()
print(extractor.get_soundcloud_tracks())
