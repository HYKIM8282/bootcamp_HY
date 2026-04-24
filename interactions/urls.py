from django.urls import path
from . import views

app_name = 'interactions'

urlpatterns = [
    # ✅ 리뷰 작성: /interactions/<agent_pk>/create/
    path('<int:agent_pk>/create/', views.review_create, name='review_create'),

    # ✅ 리뷰 삭제: /interactions/<review_pk>/delete/
    path('<int:review_pk>/delete/', views.review_delete, name='review_delete'),
]