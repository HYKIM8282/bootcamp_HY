from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

app_name = "community"

router = DefaultRouter()
router.register("posts", views.PostViewSet, basename="post")

# ─────────────────────────────────────────────────────
# ViewSet 액션 별칭 — 옛 pocket_menu.html 호환용
# (templates/community/pocket_menu.html 이 사용하던 이름)
# ─────────────────────────────────────────────────────
PostListCompat = views.PostViewSet.as_view({
    "get":  "list",
    "post": "create",
})
PostDeleteCompat = views.PostViewSet.as_view({
    "delete": "destroy",
})

urlpatterns = [
    # 게시판 페이지 (HTML) — 로그인 없이 접근
    path("", views.board_view, name="board"),

    # ViewSet 라우터 — /community/api/posts/ 등
    path("api/", include(router.urls)),

    # 레거시 호환 (pocket_menu 가 사용하는 옛 URL 이름)
    path("posts/",                 PostListCompat,   name="post_list"),
    path("posts/<int:pk>/delete/", PostDeleteCompat, name="post_delete"),
]
