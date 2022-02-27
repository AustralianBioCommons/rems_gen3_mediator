import json
import logging
import requests
from urllib.parse import urljoin

from django.core.management.base import BaseCommand

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


class Gen3Config:
    def __init__(self, server_url, auth_config):
        self.server_url = server_url
        self.auth_config = auth_config

    @staticmethod
    def from_file(server_url, creds_file):
        with open(creds_file) as f:
            return Gen3Config(server_url, json.load(f))


class RemsConfig:
    def __init__(self, server_url, user_id, api_key, organization_id, license_id):
        self.server_url = server_url
        self.user_id = user_id
        self.api_key = api_key
        self.organization_id = organization_id
        self.license_id = license_id


class Command(BaseCommand):
    help = 'Imports gen3 projects and creates corresponding resources in REMS'

    def add_arguments(self, parser):
        parser.add_argument('gen3_creds_file')
        parser.add_argument(
            '--gen3_server_url', default='https://data.acdc.ozheart.org',
            help='URL of the gen3 server API')
        parser.add_argument(
            '--rems_server_url', default='http://localhost',
            help='URL of the rems server API')
        parser.add_argument('rems_user_id')
        parser.add_argument('rems_api_key')
        parser.add_argument('rems_organization_id')
        parser.add_argument(
            '--rems_license_id', default=1, type=int,
            help='License id to use for newly created resources')

    def handle(self, *args, **options):
        gen3_config = Gen3Config.from_file(options['gen3_server_url'], options['gen3_creds_file'])
        rems_config = RemsConfig(options['rems_server_url'], options['rems_user_id'], options['rems_api_key'],
                                 options['rems_organization_id'], options['rems_license_id'])

        self.transfer_gen3_projects_to_rems(gen3_config, rems_config)

    @staticmethod
    def get_gen3_api_token(gen3_config):
        gen3_token_endpoint = urljoin(gen3_config.server_url, "/user/credentials/cdis/access_token")
        gen3_token_json = requests.post(gen3_token_endpoint, json=gen3_config.auth_config).json()
        return gen3_token_json['access_token']

    @staticmethod
    def get_gen3_projects_list(gen3_config):
        gen3_token = Command.get_gen3_api_token(gen3_config)
        headers = {"Authorization": f"Bearer {gen3_token}"}
        gen3_graphql_endpoint = urljoin(gen3_config.server_url, "/api/v0/submission/graphql/")
        response = requests.post(gen3_graphql_endpoint, data='{"query": "{project{id,name}}"}', headers=headers)
        return response.json()['data']['project']

    @staticmethod
    def get_rems_headers(rems_user_id, rems_api_key):
        return {
            'x-rems-api-key': rems_api_key,
            'x-rems-user-id': rems_user_id,
        }

    @staticmethod
    def rems_get_all_resources(rems_config):
        headers = Command.get_rems_headers(rems_config.user_id, rems_config.api_key)
        rems_resource_get_endpoint = urljoin(rems_config.server_url, "/api/resources")
        response = requests.get(rems_resource_get_endpoint, headers=headers)
        response.raise_for_status()
        return response.json()

    @staticmethod
    def rems_create_resource(rems_config, resource_urn):
        headers = Command.get_rems_headers(rems_config.user_id, rems_config.api_key)
        body = {
            "resid": resource_urn,
            "organization": {
                "organization/id": rems_config.organization_id
            },
            "licenses": [
                rems_config.license_id
            ]
        }
        rems_resource_create_endpoint = urljoin(rems_config.server_url, "/api/resources/create")
        response = requests.post(rems_resource_create_endpoint, headers=headers, json=body)
        response.raise_for_status()
        return response

    def transfer_gen3_projects_to_rems(self, gen3_config, rems_config):
        try:
            log.debug(f"Importing projects from gen3 server: {gen3_config.server_url}")
            project_urns = [f"gen3:project:{project['name']}:{project['id']}" for project in
                            self.get_gen3_projects_list(gen3_config)]
            existing_rems_urns = [resource['resid'] for resource in
                                  Command.rems_get_all_resources(rems_config)]
            urns_to_create = set(project_urns).difference(set(existing_rems_urns))
            for urn in urns_to_create:
                log.debug(f"Registering new resource with REMS: {urn}")
                self.rems_create_resource(rems_config, urn)
        except Exception as e:
            log.exception("An error occurred while importing projects:")
