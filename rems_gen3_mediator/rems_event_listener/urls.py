from django.urls import path
from .views import RemsEntitlementAdd, RemsEntitlementRemove

urlpatterns = [
    path('entitlement/add', RemsEntitlementAdd.as_view()),
    path('entitlement/remove', RemsEntitlementRemove.as_view()),
]