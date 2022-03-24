import json
import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .api import RemsMediator

logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.DEBUG)
log = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class RemsEntitlementAdd(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        log.debug(data)
        mediator = RemsMediator()
        for entitlement in data:
            mediator.add_untrusted_entitlement(entitlement['resource'], entitlement['user'], entitlement['mail'])
        return JsonResponse({'status': 'success'})


@method_decorator(csrf_exempt, name='dispatch')
class RemsEntitlementRemove(View):

    def post(self, request):
        data = json.loads(request.body.decode("utf-8"))
        mediator = RemsMediator()
        for entitlement in data:
            mediator.remove_untrusted_entitlement(entitlement['resource'], entitlement['user'], entitlement['mail'])
        return JsonResponse({'status': 'success'})

