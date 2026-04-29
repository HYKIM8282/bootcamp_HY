from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView
from django.conf import settings                        # ← 추가
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include(("brokers.urls", "brokers"), namespace="brokers")),
    path("", include(("interactions.urls", "interactions"), namespace="interactions")),
    path("", RedirectView.as_view(url="/login/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)