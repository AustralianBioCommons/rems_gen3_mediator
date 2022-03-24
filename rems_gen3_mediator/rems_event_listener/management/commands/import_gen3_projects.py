import logging
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.core.management.base import BaseCommand

from rems_event_listener.rems_client import RemsClient

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
        response = requests.post(
            gen3_graphql_endpoint, data='{"query": "{project{code,name,programs{name}}}"}', headers=headers)
        return response.json()['data']['project']

    def transfer_gen3_projects_to_rems(self):
        try:
            log.debug(f"Importing projects from gen3 server: {settings.GEN3_SERVER_URL}")
            project_urns = [f"gen3:program:{project['programs'][0]['name']}:project:{project['name']}:code:{project['code']}"
                            for project in self.get_gen3_projects_list()]
            rems_client = RemsClient()
            existing_rems_urns = [resource['resid'] for resource in rems_client.query_resources()]
            urns_to_create = set(project_urns).difference(set(existing_rems_urns))
            for urn in urns_to_create:
                log.debug(f"Registering new resource with REMS: {urn}")
                rems_client.create_resource(urn, settings.REMS_ORGANIZATION_ID, settings.REMS_LICENSE_ID)
        except Exception as e:
            log.exception("An error occurred while importing projects:")
