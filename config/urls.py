# from django.contrib import admin
# from django.urls import path, include
# from django.views.generic import RedirectView
# from django.conf import settings                        # ← 추가
# from django.conf.urls.static import static


# urlpatterns = [
#     path("admin/", admin.site.urls),
#     path("", include("accounts.urls")),
#     path("", include(("brokers.urls", "brokers"), namespace="brokers")),
#     path("", include(("interactions.urls", "interactions"), namespace="interactions")),
#     path("", RedirectView.as_view(url="/login/", permanent=False)),
#     path("", include("brokers.urls", namespace="dashboard")),# 내가추가

# ]

# if settings.DEBUG:
#     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView


urlpatterns = [
    path("admin/", admin.site.urls),

    # 회원 관련
    path("accounts/", include("accounts.urls")),

    # brokers 앱은 /brokers/ prefix 로 연결
    path("brokers/", include(("brokers.urls", "brokers"), namespace="brokers")),

    # review / interaction 쪽이 따로 있으면 그대로 유지
    path("interactions/", include("interactions.urls")),

    # 루트("/") → 대시보드로 리다이렉트 (미로그인이면 login_required가 로그인 페이지로 보냄)
    path("", RedirectView.as_view(url="/brokers/dashboard/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

