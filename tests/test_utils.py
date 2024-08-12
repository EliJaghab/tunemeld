import logging
import unittest

from playlist_etl.utils import WebDriverManager
from playlist_etl.view_count import SPOTIFY_VIEW_COUNT_XPATH


class TestWebDriverManager(unittest.TestCase):

    def setUp(self):
        self.webdriver_manager = WebDriverManager(use_proxy=True)

    def test_find_element_by_xpath(self):
        url = "https://open.spotify.com/track/4boa7Bv0VijpxoP1SHjjUb"

        self.webdriver_manager.find_element_by_xpath(url, SPOTIFY_VIEW_COUNT_XPATH)

    def tearDown(self):
        # Close the WebDriver after the test
        self.webdriver_manager.close_driver()


if __name__ == "__main__":
    # Set up logging to print out information
    logging.basicConfig(level=logging.INFO)

    # Run the tests
    unittest.main()
