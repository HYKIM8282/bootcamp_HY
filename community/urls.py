from django.urls import path

from . import views

app_name = "community"

urlpatterns = [
    # 목록 + 작성
    path("posts/",                 views.PostListCreateView.as_view(), name="post_list"),
    # 삭제
    path("posts/<int:pk>/delete/", views.PostDeleteView.as_view(),     name="post_delete"),
]
