import json
import logging
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class RemsEntitlementReceiver(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        for entitlement in data:
            self.process_entitlement(entitlement['user'], entitlement['resource'])
        return JsonResponse({'status': 'success'})

    def process_entitlement(self, user, resource):
        # don't trust the received data, as we have no auth.
        # instead, requery REMS to verify and update accordingly
        entitlement = self.rems_query_entitlement(user, resource)
        if entitlement and entitlement[0].get('resource') == resource:
            self.create_entitlement(resource, user, entitlement[0]['user']['email'])
        else:
            # no entitlement was found, so it may be a rejection.
            blacklist_entry = self.rems_query_blacklist(user, resource)
            if blacklist_entry and blacklist_entry[0]['blacklist/resource']['resource/ext-id'] == resource:
                self.revoke_entitlement(resource, user, blacklist_entry[0]['blacklist/user']['email'])

    @staticmethod
    def get_rems_headers():
        return {
            'x-rems-api-key': settings.REMS_API_KEY,
            'x-rems-user-id': settings.REMS_USER_ID
        }

    def rems_query_entitlement(self, user, resource):
        headers = self.get_rems_headers()
        rems_resource_get_endpoint = urljoin(settings.REMS_SERVER_URL, "/api/entitlements")
        response = requests.get(rems_resource_get_endpoint, headers=headers,
                                params={'user': user, 'resource': resource, 'expired': 'false'})
        response.raise_for_status()
        return response.json()

    def rems_query_blacklist(self, user, resource):
        headers = self.get_rems_headers()
        rems_resource_get_endpoint = urljoin(settings.REMS_SERVER_URL, "/api/blacklist")
        response = requests.get(rems_resource_get_endpoint, headers=headers,
                                params={'user': user, 'resource': resource})
        response.raise_for_status()
        return response.json()

    def create_entitlement(self, resource, user, email):
        log.debug(f"Granting entitlement to resource: {resource} to user: {user} with email: {email}")

    def revoke_entitlement(self, resource, user, email):
        log.debug(f"Revoking entitlement to resource: {resource} from user: {user} with email: {email}")
