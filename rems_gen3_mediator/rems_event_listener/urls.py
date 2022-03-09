from django.urls import path
from .views import RemsEntitlementAdd, RemsEntitlementRemove

urlpatterns = [
    path('entitlements/add', RemsEntitlementAdd.as_view()),
    path('entitlements/remove', RemsEntitlementRemove.as_view()),
]