import requests
from core import settings


class Cache:
    BASE_URL_TEMPLATE = "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"

    def __init__(self):
        print("[CACHE] Initializing Cache class...")
        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID or ""
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID or ""
        self.CF_API_TOKEN = settings.CF_API_TOKEN or ""

        if self.CF_ACCOUNT_ID and self.CF_NAMESPACE_ID:
            self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)
            print("[CACHE] Cache initialized with Cloudflare KV")
        else:
            self.BASE_URL = None
            print("[CACHE] Cache running in fallback mode (no Cloudflare)")

    def get(self, key):
        if not self.BASE_URL:
            return None

        try:
            url = self.BASE_URL + key
            headers = {
                "Authorization": f"Bearer {self.CF_API_TOKEN}",
                "Content-Type": "application/json",
            }
            response = requests.get(url, headers=headers)
            value = response.json().get("value")
            return value
        except Exception as e:
            print(f"[CACHE] Error getting key {key}: {e}")
            return None

    def put(self, key, value):
        if not self.BASE_URL:
            return {"success": False, "error": "Cache not configured"}

        try:
            url = self.BASE_URL + key
            headers = {
                "Authorization": f"Bearer {self.CF_API_TOKEN}",
                "Content-Type": "application/json",
            }
            response = requests.put(url, headers=headers, json={"value": value})
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[CACHE] Error putting key {key}: {e}")
            return {"success": False, "error": str(e)}
