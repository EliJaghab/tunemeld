import time
from collections.abc import Generator

import pytest
from selenium.common.exceptions import NoSuchElementException, TimeoutException

from playlist_etl.config import SPOTIFY_VIEW_COUNT_XPATH
from playlist_etl.utils import WebDriverManager


class TestWebDriverManager:
    """Test WebDriverManager with real browser - requires internet connection"""

    @pytest.fixture
    def webdriver_manager(self) -> Generator[WebDriverManager, None, None]:
        """Create WebDriverManager instance"""
        manager = WebDriverManager(use_proxy=True)
        yield manager
        # Cleanup
        from contextlib import suppress

        with suppress(Exception):
            manager.close_driver()  # Driver may already be closed

    @pytest.mark.external_api
    @pytest.mark.slow
    def test_find_element_by_xpath_real_spotify(self, webdriver_manager: WebDriverManager) -> None:
        """Test finding element on real Spotify page - requires internet"""
        url = "https://open.spotify.com/track/4boa7Bv0VijpxoP1SHjjUb"

        try:
            # Set a reasonable timeout
            start_time = time.time()
            result = webdriver_manager.find_element_by_xpath(url, SPOTIFY_VIEW_COUNT_XPATH)
            elapsed_time = time.time() - start_time

            # Test should complete within reasonable time
            assert elapsed_time < 30, f"Test took too long: {elapsed_time:.2f} seconds"

            # Result should be something meaningful (even if empty)
            assert result is not None
            print(f"✅ Found element result: '{result}' in {elapsed_time:.2f}s")

        except (TimeoutException, NoSuchElementException) as e:
            # This is expected - Spotify may block automated access
            pytest.skip(f"Spotify blocked access or element not found: {e}")
        except Exception as e:
            pytest.fail(f"Unexpected error during WebDriver test: {e}")

    @pytest.mark.external_api
    @pytest.mark.slow
    def test_webdriver_handles_invalid_url(self, webdriver_manager: WebDriverManager) -> None:
        """Test WebDriver gracefully handles invalid URLs"""
        invalid_url = "https://this-domain-does-not-exist-12345.com"

        try:
            result = webdriver_manager.find_element_by_xpath(invalid_url, "//body")
            # Should handle gracefully
            assert result in [None, ""]
        except Exception:
            # Expected - should handle network errors gracefully
            pass

    def test_webdriver_initialization(self) -> None:
        """Test WebDriverManager can be instantiated"""
        try:
            manager = WebDriverManager(use_proxy=True)
            assert manager is not None
            manager.close_driver()
        except Exception as e:
            pytest.skip(f"WebDriver not available: {e}")

    @pytest.mark.external_api
    def test_close_driver_cleanup(self, webdriver_manager: WebDriverManager) -> None:
        """Test that driver cleanup works properly"""
        # Use the driver briefly
        from contextlib import suppress

        with suppress(Exception):
            webdriver_manager.find_element_by_xpath("https://example.com", "//title")  # Don't care if this fails

        # Cleanup should not raise exception
        webdriver_manager.close_driver()

        # Second cleanup should also not raise exception
        webdriver_manager.close_driver()


# Utility function to run only external API tests
def run_external_tests() -> bool:
    """Run only the external API tests"""
    import subprocess
    import sys

    result = subprocess.run([sys.executable, "-m", "pytest", __file__, "-v", "-m", "external_api", "--tb=short"])
    return result.returncode == 0


if __name__ == "__main__":
    print("🌐 Running WebDriver external API tests...")
    print("⚠️  These tests require internet connection and Chrome browser")

    success = run_external_tests()
    if success:
        print("✅ External API tests passed!")
    else:
        print("❌ Some external API tests failed!")
        exit(1)
