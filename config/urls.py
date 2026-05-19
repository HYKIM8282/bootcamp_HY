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
from django.views.generic import RedirectView, TemplateView


urlpatterns = [
    path("admin/", admin.site.urls),

    # 회원 관련
    path("accounts/", include("accounts.urls")),

    # brokers 앱은 /brokers/ prefix 로 연결
    path("brokers/", include(("brokers.urls", "brokers"), namespace="brokers")),

    # review / interaction 쪽이 따로 있으면 그대로 유지
    path("interactions/", include("interactions.urls")),

    # 커뮤니티 (게시판/CRUD API)
    path("community/", include(("community.urls", "community"), namespace="community")),

    # 게이트웨이 (시작 페이지) — 로그인 없이 접근 가능
    path("gateway/", TemplateView.as_view(template_name="gateway.html"), name="gateway"),

    # 루트("/") → 게이트웨이로 리다이렉트
    path("", RedirectView.as_view(url="/gateway/", permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

