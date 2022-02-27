import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .rems_client import RemsClient

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
        rems_client = RemsClient()
        entitlement = rems_client.query_entitlements(user, resource)
        if entitlement and entitlement[0].get('resource') == resource:
            self.create_entitlement(resource, user, entitlement[0]['user']['email'])
        else:
            # no entitlement was found, so it may be a rejection.
            blacklist_entry = rems_client.rems_query_blacklist(user, resource)
            if blacklist_entry and blacklist_entry[0]['blacklist/resource']['resource/ext-id'] == resource:
                self.revoke_entitlement(resource, user, blacklist_entry[0]['blacklist/user']['email'])

    def create_entitlement(self, resource, user, email):
        log.debug(f"Granting entitlement to resource: {resource} to user: {user} with email: {email}")

    def revoke_entitlement(self, resource, user, email):
        log.debug(f"Revoking entitlement to resource: {resource} from user: {user} with email: {email}")
