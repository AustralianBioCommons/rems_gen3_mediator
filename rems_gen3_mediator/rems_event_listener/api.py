import logging
import yaml

from django.conf import settings

import fasteners

from .rems_client import RemsClient

log = logging.getLogger(__name__)


GEN3_USER_LOCK_FILE = '/tmp/gen3_user_lock'


class RemsMediator:

    def add_untrusted_entitlement(self, resource, user, email):
        # don't trust the received data, as we have no auth.
        # instead, requery REMS to verify and update accordingly
        rems_client = RemsClient()
        entitlement = rems_client.query_entitlements(user, resource)
        if entitlement and entitlement[0].get('resource') == resource:
            self.create_entitlement(resource, user, entitlement[0]['user']['email'])
        else:
            log.error(f"A request to add entitlement to resource: {resource} for user: {user} with email: {email}"
                      "could not be fulfilled because the request could not be verified against REMS")

    def remove_untrusted_entitlement(self, resource, user, email):
        # don't trust the received data, as we have no auth.
        # instead, requery REMS to verify and update accordingly
        rems_client = RemsClient()
        blacklist_entry = rems_client.query_blacklist(user, resource)
        if blacklist_entry and blacklist_entry[0]['blacklist/resource']['resource/ext-id'] == resource:
            self.revoke_entitlement(resource, user, blacklist_entry[0]['blacklist/user']['email'])
        else:
            log.error(f"A request to remove entitlement to resource: {resource} for user: {user} with email: {email}"
                      "could not be fulfilled because the request could not be verified against REMS")

    @fasteners.interprocess_locked(GEN3_USER_LOCK_FILE)
    def create_entitlement(self, resource, user, email):
        log.debug(f"Granting entitlement to resource: {resource} to user: {user} with email: {email}")
        with open(settings.GEN3_USER_CONFIG_FILE, "r+") as gen3_user_file_read:
            gen3_user_data = yaml.safe_load(gen3_user_file_read) or {}
        with open(settings.GEN3_USER_CONFIG_FILE, "w+") as gen3_user_file_write:
            users = gen3_user_data.get('users', {})
            if email not in users:
                users[email] = {
                    'tags': {
                        'name': user
                    },
                    'policies': []
                }
                gen3_user_data['users'] = users
                yaml.safe_dump(gen3_user_data, gen3_user_file_write)

    @fasteners.interprocess_locked(GEN3_USER_LOCK_FILE)
    def revoke_entitlement(self, resource, user, email):
        log.debug(f"Revoking entitlement to resource: {resource} from user: {user} with email: {email}")
        with open(settings.GEN3_USER_CONFIG_FILE, "r+") as gen3_user_file_read:
            gen3_user_data = yaml.safe_load(gen3_user_file_read) or {}
        with open(settings.GEN3_USER_CONFIG_FILE, "w+") as gen3_user_file_write:
            users = gen3_user_data.get('users', {})
            if email in users:
                del users[email]
                gen3_user_data['users'] = users
                yaml.safe_dump(gen3_user_data, gen3_user_file_write)
