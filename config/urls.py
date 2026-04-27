from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include(("brokers.urls", "brokers"), namespace="brokers")),
    path("", include(("interactions.urls", "interactions"), namespace="interactions")),
    path("", RedirectView.as_view(url="/login/", permanent=False)),
]