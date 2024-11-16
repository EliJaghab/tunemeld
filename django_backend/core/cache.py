import requests
from core import settings


class CloudflareKV:
    BASE_URL_TEMPLATE = (
        "https://api.cloudflare.com/client/v4/accounts/{}/storage/kv/namespaces/{}/values/"
    )

    def __init__(self):
        self.CF_ACCOUNT_ID = settings.CF_ACCOUNT_ID
        self.CF_NAMESPACE_ID = settings.CF_NAMESPACE_ID
        self.CF_API_TOKEN = settings.CF_API_TOKEN
        self.BASE_URL = self.BASE_URL_TEMPLATE.format(self.CF_ACCOUNT_ID, self.CF_NAMESPACE_ID)

    def get_kv_entry(self, key):
        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None

    def put_kv_entry(self, key, value):
        url = self.BASE_URL + key
        headers = {
            "Authorization": f"Bearer {self.CF_API_TOKEN}",
            "Content-Type": "application/json",
        }
        response = requests.put(url, headers=headers, json={"value": value})
        if response.status_code == 200:
            return response.json()
        return None
