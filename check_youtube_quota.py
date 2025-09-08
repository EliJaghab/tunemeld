#!/usr/bin/env python3

import os
import sys
from datetime import datetime

import requests

sys.path.append("django_backend")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django

django.setup()


def check_youtube_quota():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not found!")
        return

    print("📊 YouTube API Quota Investigation")
    print("=" * 50)

    # Test a simple search to see the exact error response
    test_query = "test"
    search_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={test_query}&key={api_key}&maxResults=1"

    try:
        print(f"🔍 Testing search with query: '{test_query}'")
        response = requests.get(search_url)

        print(f"📡 Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print("✅ API call successful!")
            print(f"📊 Results found: {data.get('pageInfo', {}).get('totalResults', 0)}")

            if "quotaUser" in data:
                print(f"👤 Quota user: {data['quotaUser']}")

        else:
            print(f"❌ API call failed: {response.status_code}")
            try:
                error_data = response.json()
                print("📝 Error details:")
                if "error" in error_data:
                    error = error_data["error"]
                    print(f"   Code: {error.get('code')}")
                    print(f"   Message: {error.get('message')}")

                    if "errors" in error:
                        for err in error["errors"]:
                            print(f"   Reason: {err.get('reason')}")
                            print(f"   Domain: {err.get('domain')}")
            except:
                print(f"📝 Raw error response: {response.text}")

        # Check response headers for quota info
        print("\n📋 Response headers:")
        relevant_headers = ["x-ratelimit", "x-quota", "retry-after", "content-type"]
        for header, value in response.headers.items():
            if any(keyword in header.lower() for keyword in relevant_headers):
                print(f"   {header}: {value}")

    except Exception as e:
        print(f"💥 Exception occurred: {e}")

    print(f"\n🕐 Test performed at: {datetime.now()}")
    print("\n💡 Troubleshooting tips:")
    print("   1. Check Google Cloud Console for quota usage")
    print("   2. Verify API key has YouTube Data API enabled")
    print("   3. Check if billing is enabled (may increase quota)")
    print("   4. Consider requesting quota extension")


if __name__ == "__main__":
    check_youtube_quota()
