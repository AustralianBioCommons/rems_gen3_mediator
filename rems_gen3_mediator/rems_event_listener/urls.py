from django.urls import path
from .views import RemsEntitlementReceiver

urlpatterns = [
    path('', RemsEntitlementReceiver.as_view()),
]