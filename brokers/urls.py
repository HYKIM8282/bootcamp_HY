from django.urls import path
from .views import WorldAPIViewSet

urlpatterns = [
    path('world/', WorldAPIViewSet.as_view({'get': 'list'})),
]