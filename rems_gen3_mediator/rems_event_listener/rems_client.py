import requests
from urllib.parse import urljoin

from django.conf import settings


class RemsClient:

    def __init__(self, server_url: str = None, api_key: str = None, user_id: str = None):
        self.server_url = server_url or settings.REMS_SERVER_URL
        self.api_key = api_key or settings.REMS_API_KEY
        self.user_id = user_id or settings.REMS_USER_ID

    def get_rems_headers(self) -> dict:
        return {
            'x-rems-api-key': self.api_key,
            'x-rems-user-id': self.user_id
        }

    def make_get_request(self, endpoint: str, params: dict = {}) -> dict:
        headers = self.get_rems_headers()
        rems_resource_get_endpoint = urljoin(self.server_url, endpoint)
        response = requests.get(rems_resource_get_endpoint, headers=headers, params=params)
        response.raise_for_status()
        return response.json()

    def make_post_request(self, endpoint: str, params: dict = {}, body: dict = {}) -> dict:
        headers = self.get_rems_headers()
        rems_resource_get_endpoint = urljoin(self.server_url, endpoint)
        response = requests.post(rems_resource_get_endpoint, headers=headers, params=params, json=body)
        response.raise_for_status()
        return response.json()

    def query_entitlements(self, user: str = None, resource: str = None):
        return self.make_get_request('/api/entitlements',
                                     params={'user': user, 'resource': resource, 'expired': 'false'})

    def query_blacklist(self, user: str = None, resource: str = None):
        return self.make_get_request('/api/blacklist',
                                     params={'user': user, 'resource': resource})

    def query_resources(self):
        return self.make_get_request('/api/resources')

    def create_resource(self, resource_urn: str, organization_id: str, license_id: int):
        body = {
            "resid": resource_urn,
            "organization": {
                "organization/id": organization_id
            },
            "licenses": [
                license_id
            ]
        }
        return self.make_post_request('/api/resources/create', body=body)
