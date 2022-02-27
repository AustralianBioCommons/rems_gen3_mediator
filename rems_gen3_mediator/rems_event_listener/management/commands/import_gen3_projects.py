import logging
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Imports gen3 projects and creates corresponding resources in REMS'

    def handle(self, *args, **options):
        self.transfer_gen3_projects_to_rems()

    @staticmethod
    def get_gen3_api_token():
        gen3_token_endpoint = urljoin(settings.GEN3_SERVER_URL, "/user/credentials/cdis/access_token")
        gen3_token_json = requests.post(gen3_token_endpoint, json=settings.GEN3_AUTH_CONFIG).json()
        return gen3_token_json['access_token']

    @staticmethod
    def get_gen3_projects_list():
        gen3_token = Command.get_gen3_api_token()
        headers = {"Authorization": f"Bearer {gen3_token}"}
        gen3_graphql_endpoint = urljoin(settings.GEN3_SERVER_URL, "/api/v0/submission/graphql/")
        response = requests.post(gen3_graphql_endpoint, data='{"query": "{project{id,name}}"}', headers=headers)
        return response.json()['data']['project']

    @staticmethod
    def get_rems_headers():
        return {
            'x-rems-api-key': settings.REMS_API_KEY,
            'x-rems-user-id': settings.REMS_USER_ID
        }

    @staticmethod
    def rems_get_all_resources():
        headers = Command.get_rems_headers()
        rems_resource_get_endpoint = urljoin(settings.REMS_SERVER_URL, "/api/resources")
        response = requests.get(rems_resource_get_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def rems_create_resource(resource_urn):
        headers = Command.get_rems_headers()
        body = {
            "resid": resource_urn,
            "organization": {
                "organization/id": settings.REMS_ORGANIZATION_ID
            },
            "licenses": [
                settings.REMS_LICENSE_ID
            ]
        }
        rems_resource_create_endpoint = urljoin(settings.REMS_SERVER_URL, "/api/resources/create")
        response = requests.post(rems_resource_create_endpoint, headers=headers, json=body)
        response.raise_for_status()
        return response

    def transfer_gen3_projects_to_rems(self):
        try:
            log.debug(f"Importing projects from gen3 server: {settings.GEN3_SERVER_URL}")
            project_urns = [f"gen3:project:{project['name']}:{project['id']}" for project in
                            self.get_gen3_projects_list()]
            existing_rems_urns = [resource['resid'] for resource in
                                  Command.rems_get_all_resources()]
            urns_to_create = set(project_urns).difference(set(existing_rems_urns))
            for urn in urns_to_create:
                log.debug(f"Registering new resource with REMS: {urn}")
                self.rems_create_resource(urn)
        except Exception as e:
            log.exception("An error occurred while importing projects:")
