import requests
from core import settings


class Cache:
    BASE_URL_TEMPLATE = (
        "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"
    )

    def __init__(self):
        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID
        self.CF_API_TOKEN = settings.CF_API_TOKEN
        self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)

    def get(self, key):
        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)

        value = response.json().get("value")
        if not value:
            return None

        return value

    def put(self, key, value):
        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.put(url, headers=headers, json={"value": value})
        response.raise_for_status()
        return response.json()
