#!/usr/bin/env python3
"""
Credential validation script for TuneMeld.

This script validates that all required API credentials are working properly.
It's designed to run in pre-commit hooks to catch credential issues early.
"""

import argparse
import os
import sys

import requests
from pymongo import MongoClient
from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials


class CredentialValidator:
    """Validates API credentials and services."""

    def __init__(self, env_file: str | None = None):
        """Initialize validator with optional env file."""
        if env_file and os.path.exists(env_file):
            self._load_env_file(env_file)

        self.errors: list[str] = []
        self.warnings: list[str] = []

    def _load_env_file(self, env_file: str):
        """Load environment variables from file."""
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and "=" in line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value

    def validate_django_secret_key(self) -> bool:
        """Validate Django SECRET_KEY is present and secure."""
        secret_key = os.getenv("SECRET_KEY")

        if not secret_key:
            self.errors.append("SECRET_KEY environment variable is missing")
            return False

        if len(secret_key) < 32:
            self.errors.append("SECRET_KEY is too short (minimum 32 characters)")
            return False

        if secret_key.startswith("django-insecure-"):
            self.warnings.append("SECRET_KEY has 'django-insecure-' prefix - ensure this is not production")

        return True

    def validate_mongodb(self) -> bool:
        """Validate MongoDB connection and credentials."""
        mongo_uri = os.getenv("MONGO_URI")
        mongo_db_name = os.getenv("MONGO_DB_NAME")
        mongo_api_key = os.getenv("MONGO_DATA_API_KEY")
        mongo_api_endpoint = os.getenv("MONGO_DATA_API_ENDPOINT")

        if not all([mongo_uri, mongo_db_name]):
            self.errors.append("MongoDB credentials incomplete (MONGO_URI, MONGO_DB_NAME required)")
            return False

        try:
            # Test MongoDB connection
            client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            client.admin.command("ismaster")

            # Test database access
            db = client[mongo_db_name]
            db.list_collection_names()

            # Test Data API if credentials provided
            if mongo_api_key and mongo_api_endpoint:
                headers = {"api-key": mongo_api_key, "Content-Type": "application/json"}
                test_payload = {"dataSource": "tunemeld", "database": mongo_db_name, "collection": "test"}

                response = requests.post(
                    f"{mongo_api_endpoint}/action/findOne", json=test_payload, headers=headers, timeout=10
                )

                if response.status_code not in [200, 404]:
                    self.errors.append(f"MongoDB Data API test failed: {response.status_code}")
                    return False

            return True

        except Exception as e:
            self.errors.append(f"MongoDB connection failed: {e!s}")
            return False

    def validate_spotify(self) -> bool:
        """Validate Spotify API credentials."""
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not all([client_id, client_secret]):
            self.errors.append("Spotify credentials incomplete (SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET required)")
            return False

        try:
            client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
            spotify = Spotify(client_credentials_manager=client_credentials_manager)

            # Test API call
            spotify.search(q="test", type="track", limit=1)
            return True

        except SpotifyException as e:
            self.errors.append(f"Spotify API test failed: {e!s}")
            return False
        except Exception as e:
            self.errors.append(f"Spotify connection failed: {e!s}")
            return False

    def validate_youtube(self) -> bool:
        """Validate YouTube API credentials."""
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            self.errors.append("YouTube API key missing (GOOGLE_API_KEY required)")
            return False

        try:
            # Test YouTube API
            url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=test&key={api_key}&maxResults=1"
            response = requests.get(url, timeout=10)

            if response.status_code == 403:
                if "quotaExceeded" in response.text:
                    self.warnings.append("YouTube API quota exceeded - key may be valid but over limit")
                    return True
                else:
                    self.errors.append("YouTube API key invalid or access denied")
                    return False
            elif response.status_code != 200:
                self.errors.append(f"YouTube API test failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            self.errors.append(f"YouTube API connection failed: {e!s}")
            return False

    def validate_rapidapi(self) -> bool:
        """Validate RapidAPI credentials."""
        api_key = os.getenv("X_RAPIDAPI_KEY")

        if not api_key:
            self.errors.append("RapidAPI key missing (X_RAPIDAPI_KEY required)")
            return False

        # Note: We can't easily test RapidAPI without knowing specific endpoints
        # This is a basic validation that the key exists and has expected format
        if len(api_key) < 32:
            self.errors.append("RapidAPI key appears to be invalid (too short)")
            return False

        return True

    def validate_cloudflare(self) -> bool:
        """Validate Cloudflare API credentials."""
        api_token = os.getenv("CF_API_TOKEN")
        account_id = os.getenv("CF_ACCOUNT_ID")
        namespace_id = os.getenv("CF_NAMESPACE_ID")

        if not all([api_token, account_id, namespace_id]):
            self.errors.append(
                "Cloudflare credentials incomplete (CF_API_TOKEN, CF_ACCOUNT_ID, CF_NAMESPACE_ID required)"
            )
            return False

        try:
            # Test Cloudflare API
            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

            # Test account access
            response = requests.get(
                f"https://api.cloudflare.com/client/v4/accounts/{account_id}", headers=headers, timeout=10
            )

            if response.status_code == 403:
                self.errors.append("Cloudflare API token invalid or insufficient permissions")
                return False
            elif response.status_code != 200:
                self.errors.append(f"Cloudflare API test failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            self.errors.append(f"Cloudflare API connection failed: {e!s}")
            return False

    def validate_railway(self) -> bool:
        """Validate Railway API credentials."""
        api_token = os.getenv("RAILWAY_API_TOKEN")

        if not api_token:
            self.warnings.append("Railway API token missing (RAILWAY_API_TOKEN) - may not be needed for local dev")
            return True

        try:
            # Test Railway API
            headers = {"Authorization": f"Bearer {api_token}", "Content-Type": "application/json"}

            response = requests.get(
                "https://backboard.railway.app/graphql", headers=headers, json={"query": "{ me { id } }"}, timeout=10
            )

            if response.status_code == 401:
                self.errors.append("Railway API token invalid")
                return False
            elif response.status_code not in [200, 400]:  # 400 is OK for GraphQL
                self.errors.append(f"Railway API test failed: {response.status_code}")
                return False

            return True

        except Exception as e:
            self.errors.append(f"Railway API connection failed: {e!s}")
            return False

    def validate_all(self) -> bool:
        """Validate all credentials and return overall success."""
        validators = [
            ("Django SECRET_KEY", self.validate_django_secret_key),
            ("MongoDB", self.validate_mongodb),
            ("Spotify", self.validate_spotify),
            ("YouTube", self.validate_youtube),
            ("RapidAPI", self.validate_rapidapi),
            ("Cloudflare", self.validate_cloudflare),
            ("Railway", self.validate_railway),
        ]

        results = []
        for name, validator in validators:
            try:
                result = validator()
                results.append(result)
                status = "✅" if result else "❌"
                print(f"{status} {name}")
            except Exception as e:
                results.append(False)
                print(f"❌ {name} - Unexpected error: {e}")
                self.errors.append(f"{name} validation failed with unexpected error: {e}")

        # Print warnings
        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")

        # Print errors
        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"   • {error}")

        return all(results)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate TuneMeld API credentials")
    parser.add_argument("--env-file", help="Path to environment file to load (e.g., .env.dev)", default=None)
    parser.add_argument("--fail-on-warnings", action="store_true", help="Treat warnings as failures")

    args = parser.parse_args()

    print("🔍 Validating TuneMeld API credentials...")
    print("=" * 50)

    validator = CredentialValidator(args.env_file)
    success = validator.validate_all()

    if args.fail_on_warnings and validator.warnings:
        success = False

    print("=" * 50)
    if success:
        print("✅ All credential validations passed!")
        sys.exit(0)
    else:
        print("❌ Credential validation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
