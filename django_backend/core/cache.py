import requests
from core import settings


class Cache:
    BASE_URL_TEMPLATE = "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"

    def __init__(self):
        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID
        self.CF_API_TOKEN = settings.CF_API_TOKEN

        # Only set BASE_URL if we have the required credentials
        if self.CF_ACCOUNT_ID and self.CF_NAMESPACE_ID and self.CF_API_TOKEN:
            self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)
        else:
            self.BASE_URL = None

    def get(self, key):
        if not self.BASE_URL:
            return None

        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except Exception:
            return None

    def put(self, key, value):
        if not self.BASE_URL:
            return None

        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.put(url, headers=headers, json={"value": value})
            response.raise_for_status()
            return response.json()
        except Exception:
            return None
